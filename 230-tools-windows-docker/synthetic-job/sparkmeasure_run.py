"""sparkMeasure probe: does it surface the planted skew / small files? (task 230)

Rebuilds the same synthetic workload and wraps it in sparkMeasure StageMetrics.
Usage: python sparkmeasure_run.py <results_dir>
"""
import os
import sys

from pyspark.sql import SparkSession
from sparkmeasure import StageMetrics

RESULTS = sys.argv[1]
SMALL_DIR = os.path.join(RESULTS, "synthetic-job", "data", "fact_smallfiles")

spark = (
    SparkSession.builder.appName("sparkmeasure-probe")
    .config("spark.jars.packages", "ch.cern.sparkmeasure:spark-measure_2.12:0.25")
    .config("spark.jars.ivy", RESULTS + "/.ivy2")
    .config("spark.sql.adaptive.enabled", "false")
    .config("spark.sql.shuffle.partitions", "32")
    .getOrCreate()
)
sc = spark.sparkContext
sc.setLogLevel("WARN")

stagemetrics = StageMetrics(spark)

fact = spark.range(4_000_000).selectExpr(
    "id",
    "CASE WHEN id % 25 = 0 THEN CAST(rand(42) * 100 AS INT) ELSE 7 END AS k",
)
fact_local = fact.localCheckpoint()

stagemetrics.begin()

# same heavy skewed phase as synthetic_job.py
heavy_agg = (
    fact_local.selectExpr("k", "id")
    .repartition(32, "k")
    .selectExpr("k", "sha2(array_join(array_repeat(CAST(id AS STRING), 400), '-'), 256) AS h")
    .groupBy("k")
    .count()
    .orderBy("k")
)
print("heavy rows:", heavy_agg.count())

# same small-files read
fact_read = spark.read.parquet("file://" + SMALL_DIR)
print("smallfiles rows:", fact_read.count())

stagemetrics.end()
stagemetrics.print_report()
#/* CSV export via create_stagemetrics_DF + save_data */
csv = os.path.join(RESULTS, "logs", "sparkmeasure_stagemetrics.json")
print("saved", stagemetrics.save_data(stagemetrics.create_stagemetrics_DF(), csv))
print("saved", csv)
spark.stop()
