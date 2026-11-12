"""e14 - Bucketing: join two bucketed tables (8 buckets on the join key) vs plain.

With matching bucketing Spark can skip the join-side shuffles (no Exchange
under SortMergeJoin). Reports shuffle bytes from the event log + plans.
Also: gzip (non-splittable) single-file scan vs snappy multi-file scan:
tasks per stage from the event log.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import RUNS, make_spark, save, timed  # noqa: E402

import pyspark.sql.functions as F  # noqa: E402

N_FACT, N_DIM = 3_000_000, 300_000
base = RUNS / "e14_data"
base.mkdir(parents=True, exist_ok=True)
res = {}
spark = make_spark("e14_bucketing", "e14_bucketing", **{"spark.sql.autoBroadcastJoinThreshold": "-1"})

fact = (
    spark.range(N_FACT)
    .withColumn("customer_id", (F.col("id") % N_DIM).cast("int"))
    .withColumn("amount", (F.col("id") % 991).cast("double"))
    .select("id", "customer_id", "amount")
)
dim = (
    spark.range(N_DIM)
    .withColumn("customer_id", F.col("id").cast("int"))
    .withColumn("region", (F.col("id") % 30).cast("string"))
    .select("customer_id", "region")
)
fact.write.mode("overwrite").bucketBy(8, "customer_id").sortBy("customer_id").saveAsTable("fact_b")
dim.write.mode("overwrite").bucketBy(8, "customer_id").sortBy("customer_id").saveAsTable("dim_b")
fact.write.mode("overwrite").parquet(str(base / "fact_p"))
dim.write.mode("overwrite").parquet(str(base / "dim_p"))

fb, db = spark.table("fact_b"), spark.table("dim_b")
fp, dp = spark.read.parquet(str(base / "fact_p")), spark.read.parquet(str(base / "dim_p"))

print("=== bucketed join plan (look for missing Exchange under SortMergeJoin) ===")
fb.join(db, "customer_id").agg(F.sum("amount")).explain(mode="simple")
print("=== plain parquet join plan (Exchange hashpartitioning on both sides) ===")
fp.join(dp, "customer_id").agg(F.sum("amount")).explain(mode="simple")

fp.join(dp, "customer_id").agg(F.sum("amount")).write.format("noop").mode("overwrite").save()  # warm
t, _ = timed(lambda: fp.join(dp, "customer_id").agg(F.sum("amount")).write.format("noop").mode("overwrite").save())
res["plain_shuffle_join_s"] = t
fb.join(db, "customer_id").agg(F.sum("amount")).write.format("noop").mode("overwrite").save()  # warm
t, _ = timed(lambda: fb.join(db, "customer_id").agg(F.sum("amount")).write.format("noop").mode("overwrite").save())
res["bucketed_join_s"] = t
save("e14_bucketing", res)
spark.stop()

# --- gzip vs snappy: splittability of a single big file --------------------
spark = make_spark("e14_gzip_split", "e14_gzip_split")
d = spark.range(6_000_000).withColumn("k", F.col("id") % 100000).withColumn("v", (F.col("id") % 997).cast("double"))
gz = base / "one_gz"
sn = base / "snappy_blocks"
d.coalesce(1).write.mode("overwrite").option("compression", "gzip").csv(str(gz))
d.write.mode("overwrite").option("compression", "snappy").csv(str(sn))
rg = spark.read.csv(str(gz))
rs = spark.read.csv(str(sn))
rg.agg(F.count("*")).show(); rs.agg(F.count("*")).show()  # warm-up
res2 = {}
t, _ = timed(lambda: rg.agg(F.count("*"), F.sum(F.col("_c1").cast("double"))).write.format("noop").mode("overwrite").save())
res2["single_gz_scan_s"] = t
t, _ = timed(lambda: rs.agg(F.count("*"), F.sum(F.col("_c1").cast("double"))).write.format("noop").mode("overwrite").save())
res2["snappy_splittable_scan_s"] = t
res2["gz_files"] = len(list(gz.glob("*"))); res2["snappy_files"] = len(list(sn.glob("*")))
save("e14_gzip_split", res2)
spark.stop()
