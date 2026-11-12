#!/usr/bin/env python
"""Generate Spark plans, EXPLAIN outputs and a Spark event log for the 12 reviewer-test cases.

Writes artifacts under results dir; the answer key goes to artifacts/answer-key.tsv so the
reviewer inputs stay separate from the defect keys.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

R = Path("/home/walidus/ai-based-projects/idle-coordinator/data/queue/results/220-sql-spark-ai-reviewer-design")
ART = R / "artifacts"
CASES = ART / "cases"


@dataclass(frozen=True)
class Case:
    cid: str
    title: str
    sql: str


CASE_LIST: list[Case] = [
    Case("q01", "high-value orders report",
         "SELECT c.name, o.amount FROM orders o JOIN customers c ON o.region = c.country "
         "JOIN support_tickets t ON t.priority = 'HIGH' ORDER BY o.amount DESC"),
    Case("q02", "customers with recent high-priority tickets",
         "SELECT o.o_id, t.t_id, o.amount FROM orders o LEFT JOIN support_tickets t "
         "ON o.customer_id = t.customer_id WHERE t.priority = 'HIGH'"),
    Case("q03", "customers without support tickets",
         "SELECT c.customer_id, c.name FROM customers c WHERE c.customer_id NOT IN "
         "(SELECT customer_id FROM support_tickets)"),
    Case("q04", "open orders revenue",
         "SELECT o.region, SUM(o.amount) AS revenue FROM orders o WHERE o.status != 'CANCELLED' GROUP BY o.region"),
    Case("q05", "orders joined to region dimension",
         "SELECT d.region_name, COUNT(*) AS n, SUM(o.amount) AS total FROM orders o "
         "JOIN dim_regions d ON o.region = d.region_code GROUP BY d.region_name"),
    Case("q06", "orders with item quantities",
         "SELECT o.o_id, o.amount, SUM(i.qty) AS qty FROM orders o JOIN order_items i ON o.o_id = i.o_id GROUP BY o.o_id, o.amount"),
    Case("q07", "top orders overall",
         "SELECT o_id, amount, row_number() OVER (ORDER BY amount DESC) AS rn FROM orders"),
    Case("q08", "orders placed since 2024",
         "SELECT o.o_id, o.amount FROM orders o WHERE to_date(o.order_ts, 'MM/dd/yyyy') >= DATE'2024-01-01'"),
    Case("q09", "count of distinct customers ordering",
         "SELECT o.region, COUNT(DISTINCT o.customer_id) AS customers FROM orders o GROUP BY o.region"),
    Case("q10", "revenue with item joins",
         "SELECT o.o_id, SUM(o.amount) AS total FROM orders o "
         "JOIN order_items i1 ON o.o_id = i1.o_id JOIN order_items i2 ON o.o_id = i2.o_id GROUP BY o.o_id"),
    Case("q11", "net amounts with tax",
         "SELECT o_id, amount, amount * 1.23 AS gross FROM orders"),
    Case("q12", "region revenue detail",
         "SELECT o.region, o.customer_id, SUM(o.amount) AS total FROM orders o GROUP BY o.region, o.customer_id"),
]


def build(spark: SparkSession) -> None:
    spark.sql("DROP TABLE IF EXISTS t_orders")
    (spark.range(0, 50000).withColumnRenamed("id", "o_id")
     .withColumn("customer_id", (F.col("o_id") % 10000).cast("long"))
     .withColumn("status", F.when(F.col("o_id") % 97 == 0, F.lit(None).cast("string")).otherwise(F.concat(F.lit("ST_"), (F.col("o_id") % 5).cast("string"))))
     .withColumn("order_date", F.date_add(F.lit("2023-01-01").cast("date"), (F.col("o_id") % 700).cast("int")))
     .withColumn("order_ts", F.date_format(F.col("order_date"), "yyyy-MM-dd"))
     .withColumn("amount", (F.col("o_id") % 1000 + 0.5).cast("decimal(10,2)"))
     # 80% of rows in one region -> data skew invisible in the static plan
     .withColumn("region", F.when(F.col("o_id") % 5 != 0, F.lit("EU")).otherwise(F.concat(F.lit("R"), (F.col("o_id") % 4).cast("string"))))
     .write.mode("overwrite").saveAsTable("orders"))
    spark.sql("DROP TABLE IF EXISTS t_customers")
    (spark.range(0, 10000).withColumnRenamed("id", "customer_id")
     .withColumn("name", F.concat(F.lit("cust_"), F.col("customer_id").cast("string")))
     .withColumn("country", F.when(F.col("customer_id") % 5 != 0, F.lit("EU")).otherwise(F.concat(F.lit("R"), (F.col("customer_id") % 4).cast("string"))))
     .withColumn("segment", (F.col("customer_id") % 3).cast("string"))
     .write.mode("overwrite").saveAsTable("customers"))
    spark.sql("DROP TABLE IF EXISTS t_tickets")
    (spark.range(0, 30000).withColumnRenamed("id", "t_id")
     .withColumn("customer_id", F.when(F.col("t_id") % 11 == 0, F.lit(None).cast("long")).otherwise(F.col("t_id") % 10000))
     .withColumn("priority", F.when(F.col("t_id") % 7 == 0, F.lit("HIGH")).otherwise(F.lit("NORMAL")))
     .write.mode("overwrite").saveAsTable("support_tickets"))
    spark.sql("DROP TABLE IF EXISTS t_items")
    (spark.range(0, 300000).withColumnRenamed("id", "oi_id")
     .withColumn("o_id", (F.col("oi_id") % 50000).cast("long"))
     .withColumn("qty", (F.col("oi_id") % 9 + 1).cast("int"))
     .withColumn("price", (F.col("oi_id") % 50 + 1).cast("decimal(8,2)"))
     .write.mode("overwrite").saveAsTable("order_items"))
    spark.sql("DROP TABLE IF EXISTS dim_regions")
    spark.sql("CREATE TABLE dim_regions (region_code STRING, region_name STRING) USING parquet")
    spark.sql("INSERT INTO dim_regions VALUES ('EU', 'Europe'), ('R0', 'Region 0'), ('R1', 'Region 1'), ('R2', 'Region 2'), ('R3', 'Region 3')")
    spark.catalog.refreshTable("orders")
    spark.catalog.refreshTable("customers")
    spark.catalog.refreshTable("support_tickets")
    spark.catalog.refreshTable("order_items")


def dump_plans(spark: SparkSession) -> None:
    # Any: py4j JVM bridge objects are untyped from Python's side
    def jvm_explain(df: Any, mode: str) -> str:
        jvm = df._sc._jvm
        assert jvm is not None
        return str(jvm.PythonSQLUtils.explainString(df._jdf.queryExecution(), mode))

    for c in CASE_LIST:
        d = CASES / c.cid
        d.mkdir(parents=True, exist_ok=True)
        (d / "question.txt").write_text(
            "Find the defect in this query (correctness or serious performance problem).\n\n" + c.sql + "\n",
            encoding="utf-8")
        df = spark.sql(c.sql)
        (d / "explain-extended.txt").write_text(df._jdf.queryExecution().toString(), encoding="utf-8")
        (d / "explain-formatted.txt").write_text(jvm_explain(df, "formatted"), encoding="utf-8")
        (d / "explain-cost.txt").write_text(jvm_explain(df, "cost"), encoding="utf-8")


def run_skewed_action(spark: SparkSession) -> None:
    """Materialise q05 so the event log carries real skew metrics."""
    c05 = [c for c in CASE_LIST if c.cid == "q05"][0]
    spark.sql(c05.sql).collect()


def main() -> None:
    if ART.exists():
        shutil.rmtree(ART)
    shutil.rmtree(R / "spark-warehouse", ignore_errors=True)
    shutil.rmtree(R / "metastore_db", ignore_errors=True)
    CASES.mkdir(parents=True, exist_ok=True)
    el = ART / "eventlog"
    el.mkdir(parents=True, exist_ok=True)
    spark = (SparkSession.builder.master("local[2]").appName("task220-plans")
             .config("spark.sql.autoBroadcastJoinThreshold", "-1")
             .config("spark.sql.adaptive.enabled", "false")
             .config("spark.sql.shuffle.partitions", "200")
             .config("spark.eventLog.enabled", "true")
             .config("spark.eventLog.dir", el.as_uri())
             .config("spark.ui.enabled", "false")
             .config("spark.sql.warehouse.dir", str(ART / "warehouse"))
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    try:
        build(spark)
        dump_plans(spark)
        run_skewed_action(spark)
        (ART / "answer-key.tsv").write_text(
            "cid\tdefect\twhere visible (expected)\n"
            "q01\tsecond join has no equi-condition -> cartesian product with 30k support_tickets; any HIGH priority row matches every order\tplan (CartesianProduct/BroadcastNestedLoopJoin)\n"
            "q02\tLEFT JOIN defeated: WHERE t.priority='HIGH' rejects NULL right side, silently an INNER JOIN; customers without tickets disappear\tSQL semantics; optimized plan shows IsNotNull+Inner conversion\n"
            "q03\tNOT IN over nullable customer_id -> predicate is NULL for all rows -> empty result\tSQL semantics; plan shows LeftAnti with null-aware condition\n"
            "q04\tstatus != 'CANCELLED' drops NULL status rows (~1/97) from revenue\tSQL semantics only (NULL-aware anti not in plan)\n"
            "q05\tdata skew: 80% of orders have region EU -> one task gets ~80% of rows after shuffle\tNOT visible in SQL or static plan; needs runtime metrics/event log\n"
            "q06\tjoin+group on same key causes extra shuffle... actual: no defect beyond SMJ-by-config; expected finding: SMJ where both sides small; reviewer sees statistics\tplan (SortMergeJoin + row counts)\n"
            "q07\trow_number() OVER (ORDER BY ...) without PARTITION BY -> all 50k rows in one partition/task\tplan (Window with no partition spec -> single partition)\n"
            "q08\torder_ts is 'yyyy-MM-dd' but parsed as 'MM/dd/yyyy' -> to_date NULL -> empty result\tSQL semantics (needs schema/format knowledge)\n"
            "q09\tCOUNT(DISTINCT customer_id) skips NULL customer_ids (none here) -> actually fine; trap: reviewer overflags; key: no defect, control case\tcontrol case\n"
            "q10\tdouble join to order_items multiplies rows: SUM(o.amount) counts each order 6x (6 items/order squared=36x)\tSQL semantics; plan shows two joins causing fanout before aggregate\n"
            "q11\tamount*1.23 on DECIMAL -> precision growth fine; control: no real defect; expected: reviewer should NOT flag (false-positive probe)\tcontrol case\n"
            "q12\t200 shuffle partitions for ~50k rows -> tiny tasks, overhead; plan shows Exchange hashpartitioning(200)\tplan (Exchange numPartitions=200)\n",
            encoding="utf-8")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
