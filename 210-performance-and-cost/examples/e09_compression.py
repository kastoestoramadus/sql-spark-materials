"""e09 - Parquet compression codecs: none vs snappy vs gzip vs zstd.

2M rows with compressible text. Reports on-disk size and filtered-scan seconds.
gzip is also the non-splittable-codec caution (one split per file).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import RUNS, make_spark, save, timed  # noqa: E402

import pyspark.sql.functions as F  # noqa: E402

N = 2_000_000
base = RUNS / "e09_data"
spark = make_spark("e09_compression", "e09_compression")

df = (
    spark.range(N)
    .withColumn("k", F.col("id") % 100000)
    .withColumn("v", (F.col("id") % 997).cast("double"))
    .withColumn("text", F.concat(F.lit("constant-prefix-region-"), (F.col("id") % 50).cast("string")))
)
res = {}
for codec in ["none", "snappy", "gzip", "zstd"]:
    d = base / codec
    d.parent.mkdir(parents=True, exist_ok=True)
    tw, _ = timed(lambda: df.write.mode("overwrite").option("compression", codec).parquet(str(d)))
    sz = sum(p.stat().st_size for p in d.iterdir())
    r = spark.read.parquet(str(d))
    r.limit(1).count()
    t, _ = timed(lambda: r.filter((F.col("k") > 90000) & (F.col("v") > 500)).agg(F.sum("v")).write.format("noop").mode("overwrite").save())
    res[codec] = {"bytes": sz, "write_s": tw, "filter_agg_s": t}
save("e09_compression", res)
spark.stop()
