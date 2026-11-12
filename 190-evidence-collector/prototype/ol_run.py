"""Run wf_sales_daily (round-2 code, current warehouse) WITH the OpenLineage listener.

Starts ol_receiver.py on port 9500, configures the OpenLineageSparkListener with
an HTTP transport pointing at it, runs the same job logic, stops the receiver.
"""
import os
import subprocess
import sys
import time

PROTO = os.path.dirname(os.path.abspath(__file__))
JAR = os.path.join(PROTO, "jars", "openlineage-spark.jar")
VENV_PY = os.path.join(PROTO, "venv", "bin", "python")

receiver = subprocess.Popen(
    [VENV_PY, os.path.join(PROTO, "ol_receiver.py")],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
time.sleep(1)

job = r"""
import os, sys
sys.path.insert(0, os.environ["PROTO_ROOT"])
import wh
from pyspark.sql import SparkSession, functions as F

spark = (
    SparkSession.builder.appName("wf_sales_daily--olprobe")
    .config("spark.jars", os.environ["OL_JAR"])
    .config("spark.extraListeners", "io.openlineage.spark.agent.OpenLineageSparkListener")
    .config("spark.openlineage.transport.type", "http")
    .config("spark.openlineage.transport.url", "http://127.0.0.1:9500")
    .config("spark.openlineage.namespace", "toy-namespace")
    .config("spark.ui.enabled", "false")
    .config("spark.driver.host", "127.0.0.1")
    .getOrCreate()
)
raw = wh.read_table(spark, "raw_sales")
agg = (
    raw.filter(F.col("qty") > 1)
    .groupBy("id")
    .agg(F.sum("amount").alias("total_amount"), F.count("*").alias("cnt"),
         F.avg("amount").alias("avg_amount"))
)
wh.write_table(spark, "sales_summary_ol_probe", agg)
wh.read_table(spark, "sales_summary_ol_probe").count()
spark.stop()
print("ol probe job done")
"""

env = dict(os.environ)
env.update(
    {
        "PROTO_ROOT": PROTO,
        "WAREHOUSE_DIR": os.path.join(PROTO, "warehouse"),
        "CATALOG_DB": os.path.join(PROTO, "catalog", "catalog.db"),
        "OL_JAR": JAR,
        "PYSPARK_PYTHON": VENV_PY,
        # spark.jars alone is too late for extraListeners registration in local
        # mode: the driver classpath must contain the jar at JVM start.
        "PYSPARK_SUBMIT_ARGS": f"--driver-class-path {JAR} pyspark-shell",
    }
)
p = subprocess.run(
    [VENV_PY, "-c", job],
    env=env,
    capture_output=True,
    text=True,
    timeout=300,
)
print("exit", p.returncode)
print(p.stdout[-3000:])
print(p.stderr[-3000:])
time.sleep(3)  # let the last events flush
receiver.terminate()
