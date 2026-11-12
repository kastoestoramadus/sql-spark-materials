"""e01 - How to read a Spark plan: the worked example for report.md section 'reading plans'.

Builds a synthetic sales fact + small customer dimension, then prints the same
query under every explain() mode and under both join strategies
(sort-merge-shuffle vs auto-broadcast). Evidence goes to runs/e01*/out*.txt.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import RUNS, make_spark, save, timed  # noqa: E402

spark = make_spark("e01_plan_reading", "e01_plan_reading")
spark.sparkContext.setLogLevel("WARN")

out = RUNS / "e01_plan_reading" / "out.txt"
out.parent.mkdir(parents=True, exist_ok=True)


def say(*a):
    print(*a)
    with open(out, "a") as fh:
        print(*a, file=fh)


import pyspark.sql.functions as F  # noqa: E402
from pyspark.sql import Window  # noqa: E402

# --- synthetic data: 4M sale rows, 200k customers -------------------------
N_FACT, N_DIM = 4_000_000, 200_000
fact = (
    spark.range(N_FACT)
    .withColumn("customer_id", (F.col("id") % N_DIM).cast("int"))
    .withColumn("amount", (F.col("id") % 997).cast("double") / 10)
    .withColumn("dt", F.expr("date_sub(current_date(), cast(id % 365 as int))"))
    .select("id", "customer_id", "amount", "dt")
)
dim = (
    spark.range(N_DIM)
    .withColumn("customer_id", F.col("id").cast("int"))
    .withColumn("region", F.expr("concat('R', cast(id % 20 as string))"))
    .select("customer_id", "region")
)

joined = fact.join(dim, "customer_id").groupBy("region").agg(F.sum("amount").alias("revenue"))

say("=" * 70)
say("PLAN 1: default join (broadcast kicks in because dim < 10MB) - formatted mode")
say("=" * 70)
joined.explain(mode="formatted")

say("=" * 70)
say("PLAN 2: same join, broadcast forced OFF -> SortMergeJoin + two Exchanges")
say("=" * 70)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)
joined.explain(mode="formatted")

say("=" * 70)
say("PLAN 3: simple vs extended vs cost (operator details, statistics, exchanges)")
say("=" * 70)
joined.explain(mode="simple")
joined.explain(mode="extended")
joined.explain(mode="cost")

say("=" * 70)
say("PLAN 4: AQE on: final plan shows AdaptiveSparkPlan, partition coalescing")
say("=" * 70)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 10485760)
spark.conf.set("spark.sql.adaptive.enabled", "true")
joined.explain(mode="formatted")
say("--- AQE off, physical plan fragment:")
spark.conf.set("spark.sql.adaptive.enabled", "false")
joined.explain(mode="simple")

say("=" * 70)
say("PLAN 5: window function partitioned vs unpartitioned (Exchange single vs hash)")
say("=" * 70)
w_part = (
    joined.withColumn("rk", F.row_number().over(Window.partitionBy("region").orderBy(F.col("revenue").desc())))
)
w_nopart = joined.withColumn("rk", F.row_number().over(Window.orderBy(F.col("revenue").desc())))
w_nopart.explain(mode="formatted")

# also run it so the event log has the two plans as jobs
t1, _ = timed(lambda: w_part.write.format("noop").mode("overwrite").save())
t2, _ = timed(lambda: w_nopart.write.format("noop").mode("overwrite").save())
say(f"partitioned window action: {t1}s; UNPARTITIONED window action: {t2}s")
save("e01_plan_reading", {"partitioned_window_s": t1, "unpartitioned_window_s": t2})
spark.stop()
