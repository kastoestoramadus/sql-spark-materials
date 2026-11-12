"""Synthetic Spark job with two planted problems (task 230).

Planted problem 1 - skew: 96% of fact rows have k = 7 (the hot key), so the join
and the group-by on k run one long task next to many short ones.
Planted problem 2 - small files: the fact table is written as 60 tiny parquet
files (~ a few KB each) that the next read must open one by one.

Usage: python synthetic_job.py <results_dir>
"""
import os
import sys

from pyspark.sql import SparkSession

RESULTS = sys.argv[1]
DATA = os.path.join(RESULTS, "synthetic-job", "data")
os.makedirs(DATA, exist_ok=True)
os.makedirs(os.path.join(RESULTS, "logs", "spark-events35"), exist_ok=True)

spark = (
    SparkSession.builder.appName("synthetic-skew-smallfiles")
    .config("spark.eventLog.enabled", "true")
    .config("spark.eventLog.dir", "file://" + os.path.join(RESULTS, "logs", "spark-events35"))
    .config("spark.sql.adaptive.enabled", "false")
    .config("spark.sql.shuffle.partitions", "32")
    .getOrCreate()
)
sc = spark.sparkContext
sc.setLogLevel("WARN")

# ---- fact table: 4,000,000 rows, k=7 for 96% of them (planted skew) ----
fact = spark.range(4_000_000).selectExpr(
    "id",
    "CASE WHEN id % 25 = 0 THEN CAST(rand(42) * 100 AS INT) ELSE 7 END AS k",
    "id % 1000 AS payload",
)
fact_local = fact.localCheckpoint()

# ---- planted small-files problem: 60 tiny parquet files ----
small_dir = os.path.join(DATA, "fact_smallfiles")
(fact_local.limit(6000).repartition(60).write.mode("overwrite").parquet(small_dir))

# ---- dim table: 101 distinct keys ----
dim = spark.range(0, 101).selectExpr("id AS k", "CAST(id AS STRING) AS label")

# ---- the job: read many small files, skewed join, skewed aggregation ----
fact_read = spark.read.parquet(small_dir)
joined = fact_read.join(dim, "k")
agg = joined.groupBy("k").count().orderBy("k")

print("=== files in input dir ===")
print(len([f for f in os.listdir(small_dir) if f.endswith(".parquet")]), "parquet files")
sizes = [os.path.getsize(os.path.join(small_dir, f)) for f in os.listdir(small_dir) if f.endswith(".parquet")]
print("total KB:", round(sum(sizes) / 1024, 1), "avg KB/file:", round(sum(sizes) / 1024 / len(sizes), 1))
print("input partitions:", fact_read.rdd.getNumPartitions())
print("=== hot key share (k=7) ===")
fact_read.where("k = 7").count()
fact_read.createOrReplaceTempView("fact_read")
print(
    spark.sql("SELECT round(100.0 * sum(CASE WHEN k = 7 THEN 1 ELSE 0 END) / count(*), 1) AS pct_k7 FROM fact_read").collect()
)
print("=== result rows:", agg.count())
agg.show(5)

# ---- heavy phase: repartition by the skewed key, THEN hash ~700-char strings per
# row, so the reduce task holding k=7 (96% of rows) is the one long task ----
heavy_agg = (
    fact_local.selectExpr("k", "id")
    .repartition(32, "k")
    .selectExpr("k", "sha2(array_join(array_repeat(CAST(id AS STRING), 400), '-'), 256) AS h")
    .groupBy("k")
    .count()
    .orderBy("k")
)
print("=== heavy phase rows:", heavy_agg.count())
spark.stop()
