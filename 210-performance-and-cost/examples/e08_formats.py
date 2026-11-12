"""e08 - File format: CSV vs Parquet for a filtered aggregate on 2M rows.

Parquet does column pruning + predicate pushdown (pushedFilters in the Scan
node); CSV must parse every row. Reports seconds, input bytes, on-disk sizes.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import RUNS, make_spark, save, timed  # noqa: E402

import pyspark.sql.functions as F  # noqa: E402

N = 2_000_000
base = RUNS / "e08_data"
spark = make_spark("e08_formats", "e08_formats")

df = (
    spark.range(N)
    .withColumn("k", F.col("id") % 100000)
    .withColumn("payload", F.lpad(F.col("id").cast("string"), 40, "0"))
    .withColumn("v", (F.col("id") % 997).cast("double"))
)
base.mkdir(parents=True, exist_ok=True)
csv_dir, pq_dir = base / "csv", base / "pq"
df.write.mode("overwrite").option("header", "true").csv(str(csv_dir))
df.write.mode("overwrite").parquet(str(pq_dir))

sz_csv = sum(p.stat().st_size for p in csv_dir.iterdir())
sz_pq = sum(p.stat().st_size for p in pq_dir.iterdir())

c = spark.read.option("header", "true").csv(str(csv_dir))
p = spark.read.parquet(str(pq_dir))
c.limit(1).count(); p.limit(1).count()  # warm schema inference

q = lambda d: d.filter((F.col("k") > 90000) & (F.col("v") > 500)).agg(F.sum("v"))

p.explain(True)  # plan evidence: pushedFilters in Parquet Scan (see out file)
tcsv, _ = timed(lambda: q(c).write.format("noop").mode("overwrite").save())
tpq, _ = timed(lambda: q(p).write.format("noop").mode("overwrite").save())

save("e08_formats", {"csv_bytes": sz_csv, "parquet_bytes": sz_pq, "csv_filter_agg_s": tcsv, "parquet_filter_agg_s": tpq})
spark.stop()
