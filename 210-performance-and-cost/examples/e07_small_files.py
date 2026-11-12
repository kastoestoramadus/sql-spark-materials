"""e07 - Small-files problem and compaction.

Writes the same 2M-row dataset as 200 small parquet files (repartition(200))
vs 4 compacted files, then times a filtered aggregate over each layout and
counts files and listing work. Reports seconds + input bytes from event log.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import RUNS, make_spark, save, timed  # noqa: E402

import pyspark.sql.functions as F  # noqa: E402

N = 2_000_000
base = RUNS / "e07_data"
spark = make_spark("e07_small_files", "e07_small_files")

df = spark.range(N).withColumn("k", F.col("id") % 100000).withColumn("v", (F.col("id") % 997).cast("double"))

small_dir = base / "many_small"
big_dir = base / "compacted"
small_dir.parent.mkdir(parents=True, exist_ok=True)

t1, _ = timed(lambda: df.repartition(200).write.mode("overwrite").parquet(str(small_dir)))
t2, _ = timed(lambda: df.coalesce(4).write.mode("overwrite").parquet(str(big_dir)))

n_small = len(list(small_dir.glob("*.parquet")))
n_big = len(list(big_dir.glob("*.parquet")))

read_small = spark.read.parquet(str(small_dir))
read_big = spark.read.parquet(str(big_dir))
# warm-up both schemas
read_small.limit(1).count(); read_big.limit(1).count()

ta, _ = timed(lambda: read_small.filter(F.col("k") == 7).agg(F.sum("v")).write.format("noop").mode("overwrite").save())
tb, _ = timed(lambda: read_big.filter(F.col("k") == 7).agg(F.sum("v")).write.format("noop").mode("overwrite").save())

sz_small = sum(p.stat().st_size for p in small_dir.glob("*.parquet"))
sz_big = sum(p.stat().st_size for p in big_dir.glob("*.parquet"))
save(
    "e07_small_files",
    {
        "files_small": n_small, "files_compacted": n_big,
        "bytes_small": sz_small, "bytes_compacted": sz_big,
        "write_small_s": t1, "write_compacted_s": t2,
        "read_filter_agg_small_s": ta, "read_filter_agg_compacted_s": tb,
    },
)
spark.stop()
