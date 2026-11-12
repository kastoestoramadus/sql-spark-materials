"""e02 - Data skew in a join: AQE off / AQE on (skew join) / manual salting.

Synthetic: 3M fact rows whose join key is 90% one value (customer_id = 1).
Reports wall time and per-stage max vs p50 task runtime from the event log.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import make_spark, save, timed  # noqa: E402

import pyspark.sql.functions as F  # noqa: E402

N_FACT, N_DIM = 10_000_000, 100_000
SALT_BUCKETS = 8

base_conf = {"spark.sql.shuffle.partitions": "8", "spark.sql.adaptive.enabled": "false", "spark.sql.autoBroadcastJoinThreshold": "-1"}
spark = make_spark("e02_skew_aqe_off", "e02_skew_aqe_off", **base_conf)

fact = (
    spark.range(N_FACT)
    .withColumn(
        "customer_id",
        F.when(F.col("id") < N_FACT * 995 // 1000, F.lit(1)).otherwise((F.col("id") % N_DIM).cast("int")),
    )
    .withColumn("amount", (F.col("id") % 991).cast("double"))
    .select("id", "customer_id", "amount")
)
dim = spark.range(N_DIM).withColumn("customer_id", F.col("id").cast("int")).withColumn("tag", F.lit("x")).select("customer_id", "tag")

# warm JVM/codegen once with a small aggregate
fact.groupBy(F.col("customer_id") % 10).count().write.format("noop").mode("overwrite").save()

res = {}
t, n = timed(lambda: fact.join(dim, "customer_id").groupBy("tag").count().write.format("noop").mode("overwrite").save())
res["aqe_off_s"] = t
save("e02_skew_aqe_off", res)
spark.stop()

# --- variant 2: AQE on (skew join + coalescing enabled by default) --------
spark = make_spark("e02_skew_aqe_on", "e02_skew_aqe_on", **{"spark.sql.shuffle.partitions": "8", "spark.sql.adaptive.enabled": "true", "spark.sql.autoBroadcastJoinThreshold": "-1",
    "spark.sql.adaptive.skewJoin.enabled": "true", "spark.sql.adaptive.advisoryPartitionSizeInBytes": "131072", "spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes": "262144"})
fact = (
    spark.range(N_FACT)
    .withColumn(
        "customer_id",
        F.when(F.col("id") < N_FACT * 995 // 1000, F.lit(1)).otherwise((F.col("id") % N_DIM).cast("int")),
    )
    .withColumn("amount", (F.col("id") % 991).cast("double"))
    .select("id", "customer_id", "amount")
)
dim = spark.range(N_DIM).withColumn("customer_id", F.col("id").cast("int")).withColumn("tag", F.lit("x")).select("customer_id", "tag")
fact.groupBy(F.col("customer_id") % 10).count().write.format("noop").mode("overwrite").save()
t, _ = timed(lambda: fact.join(dim, "customer_id").groupBy("tag").count().write.format("noop").mode("overwrite").save())
save("e02_skew_aqe_on", {"aqe_on_s": t})
spark.stop()

# --- variant 3: manual salting, AQE off ----------------------------------
spark = make_spark("e02_skew_salt", "e02_skew_salt", **base_conf)
fact = (
    spark.range(N_FACT)
    .withColumn(
        "customer_id",
        F.when(F.col("id") < N_FACT * 995 // 1000, F.lit(1)).otherwise((F.col("id") % N_DIM).cast("int")),
    )
    .withColumn("amount", (F.col("id") % 991).cast("double"))
    .select("id", "customer_id", "amount")
)
dim = spark.range(N_DIM).withColumn("customer_id", F.col("id").cast("int")).withColumn("tag", F.lit("x")).select("customer_id", "tag")
fact.groupBy(F.col("customer_id") % 10).count().write.format("noop").mode("overwrite").save()

fact_s = fact.withColumn("salt", (F.col("id") % SALT_BUCKETS).cast("int"))
dim_s = dim.withColumn("salt", F.explode(F.sequence(F.lit(0), F.lit(SALT_BUCKETS - 1)))).withColumn(
    "customer_id", F.col("customer_id")
)
t, _ = timed(
    lambda: fact_s.join(dim_s, ["customer_id", "salt"]).groupBy("tag").count().write.format("noop").mode("overwrite").save()
)
save("e02_skew_salt", {"manual_salt_s": t})
spark.stop()
