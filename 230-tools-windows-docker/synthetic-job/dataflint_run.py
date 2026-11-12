"""DataFlint probe: attach plugin to local Spark, run skewed job, read own UI (task 230)."""
import os
import sys
import urllib.request

from pyspark.sql import SparkSession

RESULTS = sys.argv[1]
SMALL_DIR = os.path.join(RESULTS, "synthetic-job", "data", "fact_smallfiles")

spark = (
    SparkSession.builder.appName("dataflint-probe")
    .config("spark.jars.packages", "io.dataflint:spark_2.12:0.9.9")
    .config("spark.jars.ivy", RESULTS + "/.ivy2")
    .config("spark.plugins", "io.dataflint.spark.SparkDataflintPlugin")
    .config("spark.ui.port", "4040")
    .config("spark.eventLog.enabled", "true")
    .config("spark.eventLog.dir", RESULTS + "/logs/spark-events35")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("INFO")

fact = spark.range(4_000_000).selectExpr(
    "id", "CASE WHEN id % 25 = 0 THEN CAST(rand(42) * 100 AS INT) ELSE 7 END AS k"
).localCheckpoint()
heavy = (
    fact.selectExpr("k", "id")
    .repartition(32, "k")
    .selectExpr("k", "sha2(array_join(array_repeat(CAST(id AS STRING), 400), '-'), 256) AS h")
    .groupBy("k").count().orderBy("k")
)
print("heavy rows:", heavy.count())
spark.read.parquet("file://" + SMALL_DIR).count()

html = urllib.request.urlopen("http://localhost:4040/", timeout=15).read().decode()
print("UI served:", len(html), "bytes; DataFlint tab present:", "dataflint" in html.lower())
import re
tabs = re.findall(r'href="(/[^"]*)"', html)
print("tabs:", sorted(set(t for t in tabs if not t.startswith("/api") and "." not in t))[:15])
spark.stop()
