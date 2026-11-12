"""e12 - Window without partitionBy, accidental cartesian/nested-loop, collect().

Three classic antipatterns, measured on millions of rows:
  W1) row_number() over Window.partitionBy(k)   -> hash Exchange, parallel
  W2) row_number() over Window.orderBy(...)     -> Exchange SinglePartition:
      the whole dataset moves through ONE task (parallelism 1, OOM risk).
  X)  join with a non-equality condition        -> BroadcastNestedLoopJoin,
      output = |left| x |right| rows
  C)  collect() of a large result vs write to parquet.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import RUNS, make_spark, save, timed  # noqa: E402

import pyspark.sql.functions as F  # noqa: E402
from pyspark.sql import Window  # noqa: E402

N = 3_000_000
res = {}
spark = make_spark("e12_window", "e12_window")

df = (
    spark.range(N)
    .withColumn("k", F.col("id") % 50000)
    .withColumn("v", (F.col("id") % 977).cast("double"))
)
# warm-up codegen
df.withColumn("rk", F.row_number().over(Window.partitionBy("k").orderBy(F.col("v").desc()))).limit(1).count()

# full materialisation (filter would let TakeOrderedAndProject bypass the window)
w1 = df.withColumn("rk", F.row_number().over(Window.partitionBy("k").orderBy(F.col("v").desc())))
t, _ = timed(lambda: w1.select("id", "rk").write.format("noop").mode("overwrite").save())
res["window_partitioned_s"] = t

w2 = df.withColumn("rk", F.row_number().over(Window.orderBy(F.col("v").desc())))
t, _ = timed(lambda: w2.select("id", "rk").write.format("noop").mode("overwrite").save())
res["window_single_partition_s"] = t

save("e12_window", res)
spark.stop()

# --- nested-loop (cartesian) join: 500k x 500 ----------------------------
spark = make_spark("e12_cartesian", "e12_cartesian")
left = spark.range(500_000).withColumn("a", (F.col("id") % 1000).cast("int"))
right = spark.range(500).withColumn("b", (F.col("id") % 100).cast("int"))
left.join(right, left.a > right.b).limit(1).count()  # warm-up
t, _ = timed(lambda: left.join(right, left.a > right.b).agg(F.count("*")).write.format("noop").mode("overwrite").save())
save("e12_cartesian", {"nested_loop_500k_x_500_count_s": t})
print("plan for the inequality join:")
left.join(right, left.a > right.b).explain(mode="simple")
spark.stop()

# --- collect on a large result vs write -----------------------------------
spark = make_spark("e12_collect", "e12_collect")
big = spark.range(2_000_000).withColumn("v", (F.col("id") % 977).cast("double"))
big.agg(F.sum("v")).show()  # warm-up
res2 = {}
t, _ = timed(lambda: len(big.select("id", "v").collect()))
res2["collect_2m_rows_s"] = t
outp = RUNS / "e12_collect" / "out_parquet"
t, _ = timed(lambda: big.select("id", "v").write.mode("overwrite").parquet(str(outp)))
res2["write_parquet_2m_rows_s"] = t
res2["note"] = "collect() serialises every row through the driver; write keeps data distributed"
save("e12_collect", res2)
spark.stop()
