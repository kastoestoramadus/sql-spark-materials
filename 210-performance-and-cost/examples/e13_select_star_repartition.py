"""e13 - Wide select * and repartition misuse.

S1) read 3 needed columns of a 40-column wide parquet table vs select * then
    use 3: measures input bytes (column pruning) and seconds.
R1) unnecessary repartition(200) before a write vs coalesce(4)/plain write:
    shuffle bytes and file count.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import RUNS, make_spark, save, timed  # noqa: E402

import pyspark.sql.functions as F  # noqa: E402

N = 2_000_000
res = {}
base = RUNS / "e13_data"
base.mkdir(parents=True, exist_ok=True)
spark = make_spark("e13_wide", "e13_wide")

cols = [(f"c{i}", (F.col("id") % (i + 97)).cast("double")) for i in range(39)]
df = spark.range(N).withColumn("k", F.col("id") % 100000)
for name, expr in cols:
    df = df.withColumn(name, expr)
wide_dir = base / "wide40"
df.write.mode("overwrite").parquet(str(wide_dir))

r = spark.read.parquet(str(wide_dir))
r.limit(1).count()

q_needed = r.select("k", "c0", "c1").filter(F.col("k") > 90000)
q_star = r.select("*").filter(F.col("k") > 90000)
q_needed.limit(1).count(); q_star.limit(1).count()  # warm

w3 = base / "write3"
ws = base / "writestar"
t, _ = timed(lambda: q_needed.write.mode("overwrite").parquet(str(w3))); res["write_3_cols_s"] = t; res["write_3_cols_bytes"] = sum(p.stat().st_size for p in w3.glob("*.parquet"))
t, _ = timed(lambda: q_star.write.mode("overwrite").parquet(str(ws))); res["select_star_write_s"] = t; res["select_star_write_bytes"] = sum(p.stat().st_size for p in ws.glob("*.parquet"))

save("e13_wide", res)
spark.stop()

# --- repartition misuse ----------------------------------------------------
spark = make_spark("e13_repartition", "e13_repartition")
d = spark.range(N).withColumn("k", F.col("id") % 100000).withColumn("v", (F.col("id") % 997).cast("double"))
d.limit(1).count()

p1 = base / "repart200"
p2 = base / "coalesce4"
t, _ = timed(lambda: d.repartition(200).write.mode("overwrite").parquet(str(p1))); r200 = t
n200 = len(list(p1.glob("*.parquet")))
t, _ = timed(lambda: d.coalesce(4).write.mode("overwrite").parquet(str(p2))); c4 = t
n4 = len(list(p2.glob("*.parquet")))
save("e13_repartition", {"repartition200_write_s": r200, "files_repart200": n200, "coalesce4_write_s": c4, "files_coalesce4": n4})
spark.stop()
