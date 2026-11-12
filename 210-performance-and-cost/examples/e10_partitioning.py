"""e10 - Partition pruning and the implicit-cast trap.

Dataset partitioned by year (3 years). Three filters over 6M rows:
  A) filter on partition column with a proper literal  -> 1/3 of files read
  B) no partition filter (filter on value column only) -> full scan
  C) cast(year as int) = 2024 in the filter             -> pruning defeated
     (cast on the partition column makes the filter non-pushable).
Reports seconds and input bytes/records from the event log; prints the
PartitionFilters / PushedFilters lines from the explain output.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import RUNS, make_spark, save, timed  # noqa: E402

import pyspark.sql.functions as F  # noqa: E402

N = 6_000_000
base = RUNS / "e10_data"
spark = make_spark("e10_partitioning", "e10_partitioning")

df = (
    spark.range(N)
    .withColumn("year", (2022 + (F.col("id") % 3)).cast("string"))
    .withColumn("k", F.col("id") % 200000)
    .withColumn("v", (F.col("id") % 991).cast("double"))
)
base.mkdir(parents=True, exist_ok=True)
df.write.mode("overwrite").partitionBy("year").parquet(str(base))

r = spark.read.parquet(str(base))
r.limit(1).count()

out = RUNS / "e10_partitioning" / "plans.txt"


def note(*a):
    print(*a)
    with open(out, "a") as fh:
        print(*a, file=fh)


res = {}

# A: proper partition-column filter
qa = r.filter(F.col("year") == "2023").agg(F.sum("v"))
note("=== A) partition filter year='2023' ==="); qa.explain(True)
ta, _ = timed(lambda: qa.write.format("noop").mode("overwrite").save()); res["pruned_s"] = ta

# B: no partition filter
qb = r.filter(F.col("k") > 190000).agg(F.sum("v"))
note("=== B) no partition filter ==="); qb.explain(True)
tb, _ = timed(lambda: qb.write.format("noop").mode("overwrite").save()); res["full_scan_s"] = tb

# C: cast around the partition column defeats pruning
qc = r.filter(F.col("year").cast("int") == 2023).agg(F.sum("v"))
note("=== C) cast(year as int)=2023 ==="); qc.explain(True)
tc, _ = timed(lambda: qc.write.format("noop").mode("overwrite").save()); res["cast_defeats_s"] = tc

# D: function-wrapped filter on a data column defeats parquet pushdown
qd = r.filter(F.col("k").cast("string") == "95000").agg(F.sum("v"))
note("=== D) cast(k as string)='95000' (function around column) ==="); qd.explain(True)
td, _ = timed(lambda: qd.write.format("noop").mode("overwrite").save()); res["col_cast_pushdown_s"] = td

qe = r.filter(F.col("k") == 95000).agg(F.sum("v"))
note("=== E) plain k = 95000 (pushable) ==="); qe.explain(True)
te, _ = timed(lambda: qe.write.format("noop").mode("overwrite").save()); res["col_plain_s"] = te

save("e10_partitioning", res)
spark.stop()
