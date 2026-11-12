"""Seed the warehouse (schema v1) and the SQLite catalog."""
import os
import sys

PROTO = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("PROTO_ROOT", PROTO)
os.environ.setdefault("WAREHOUSE_DIR", os.path.join(PROTO, "warehouse"))
os.environ.setdefault("CATALOG_DB", os.path.join(PROTO, "catalog", "catalog.db"))
os.makedirs(os.environ["WAREHOUSE_DIR"], exist_ok=True)
os.makedirs(os.path.dirname(os.environ["CATALOG_DB"]), exist_ok=True)
sys.path.insert(0, PROTO)
import wh  # noqa: E402

from pyspark.sql import SparkSession  # noqa: E402

spark = (
    SparkSession.builder.appName("seed-warehouse")
    .config("spark.ui.enabled", "false")
    .config("spark.driver.host", "127.0.0.1")
    .getOrCreate()
)

raw = spark.createDataFrame(
    [(1, 10.0, 1), (1, 25.0, 3), (2, 200.0, 5), (3, 7.5, 2), (3, 300.0, 4), (4, 99.0, 2)],
    "id int, amount double, qty int",
)
print("seed raw_sales ->", wh.write_table(spark, "raw_sales", raw))

cust = spark.createDataFrame(
    [(1, "ann"), (2, "bo"), (3, "cy"), (4, "dee")], "id int, name string"
)
print("seed customers ->", wh.write_table(spark, "customers", cust))
spark.stop()
