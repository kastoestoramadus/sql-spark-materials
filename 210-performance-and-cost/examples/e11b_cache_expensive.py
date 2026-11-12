"""e11b - Cache when the lineage is expensive: a shuffle (window) before reuse.

Three actions over a window-derived column: without cache the window shuffle
runs three times; with cache once. This is the case where caching pays.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import RUNS, make_spark, save, timed  # noqa: E402

import pyspark.sql.functions as F  # noqa: E402
from pyspark.sql import Window  # noqa: E402

N = 3_000_000
res = {}
spark = make_spark("e11b_cache_expensive", "e11b_cache_expensive")
base = RUNS / "e11b_data"
base.mkdir(parents=True, exist_ok=True)

spark.range(N).withColumn("k", F.col("id") % 50000).withColumn("v", (F.col("id") % 991).cast("double")).write.mode(
    "overwrite"
).parquet(str(base))

src = spark.read.parquet(str(base))
w = Window.partitionBy("k").orderBy(F.col("v").desc())
df = src.withColumn("rk", F.row_number().over(w)).withColumn("pct", F.col("v") / (F.col("rk") + 1))
df.limit(1).count()  # warm-up

acts = [
    lambda: df.agg(F.sum("pct")).write.format("noop").mode("overwrite").save(),
    lambda: df.filter(F.col("rk") == 1).agg(F.avg("pct")).write.format("noop").mode("overwrite").save(),
    lambda: df.groupBy("rk").agg(F.count("*")).write.format("noop").mode("overwrite").save(),
]

t, _ = timed(lambda: [a() for a in acts])
res["no_cache_expensive_lineage_three_actions_s"] = t

df.cache()
t, _ = timed(lambda: [a() for a in acts])
res["cached_expensive_lineage_three_actions_s"] = t
save("e11b_cache_expensive", res)
spark.stop()
