"""e11 - Recomputation without cache vs cache: three actions on one lineage.

6M-row parquet source with a non-trivial derived column, consumed by three
actions. Without cache the parquet scan + derivation runs three times;
with cache once. (Local disk is fast: on cloud object storage the gap grows.)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import RUNS, make_spark, save, timed  # noqa: E402

import pyspark.sql.functions as F  # noqa: E402

N = 6_000_000
spark = make_spark("e11_cache", "e11_cache")
res = {}
base = RUNS / "e11_data"
base.mkdir(parents=True, exist_ok=True)

spark.range(N).withColumn("k", F.col("id") % 300000).withColumn("v", (F.col("id") % 991).cast("double")).write.mode(
    "overwrite"
).parquet(str(base))

df = spark.read.parquet(str(base)).withColumn("v2", F.expr("v * v + sqrt(v + 1) + log2(v + 2)"))
df.agg(F.sum("v2")).write.format("noop").mode("overwrite").save()  # warm-up

acts = [
    lambda: df.agg(F.sum("v2")).write.format("noop").mode("overwrite").save(),
    lambda: df.groupBy("k").agg(F.avg("v2").alias("m")).filter(F.col("m") > 0).count(),
    lambda: df.filter(F.col("v2") > 900).agg(F.stddev("v2")).write.format("noop").mode("overwrite").save(),
]

# --- variant 1: no cache, three actions -----------------------------------
t, _ = timed(lambda: [a() for a in acts])
res["no_cache_three_actions_s"] = t

# --- variant 2: cache, three actions --------------------------------------
df.cache()
t, _ = timed(lambda: [a() for a in acts])
res["cached_three_actions_s"] = t
res["storage_level"] = str(df.storageLevel)

save("e11_cache", res)
spark.stop()
