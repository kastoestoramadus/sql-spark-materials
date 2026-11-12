"""Platform DDL between rounds: recreate customers WITH a segment column (v2).

This happens outside any workflow and writes no workflow event log: the catalog
is the only witness of the new version, and the OLD schema survives only inside
round-1 event logs (ReadSchema).
"""
import os
import sys

PROTO = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("PROTO_ROOT", PROTO)
os.environ.setdefault("WAREHOUSE_DIR", os.path.join(PROTO, "warehouse"))
os.environ.setdefault("CATALOG_DB", os.path.join(PROTO, "catalog", "catalog.db"))
sys.path.insert(0, PROTO)
import wh  # noqa: E402

from pyspark.sql import SparkSession  # noqa: E402

spark = (
    SparkSession.builder.appName("schema-change-ddl")
    .config("spark.ui.enabled", "false")
    .config("spark.driver.host", "127.0.0.1")
    .getOrCreate()
)
cust2 = spark.createDataFrame(
    [(1, "ann", "retail"), (2, "bo", "sme"), (3, "cy", "retail"), (4, "dee", "private")],
    "id int, name string, segment string",
)
print("customers after DDL ->", wh.write_table(spark, "customers", cust2))
spark.stop()
