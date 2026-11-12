"""Run the cross-version query list on this venv's Spark (3.5).

Usage: ../venv/py3/bin/python cross_version.py   (from repro/)
Writes outputs/000-cross-spark3.txt
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from common import OUT, run_cross  # noqa: E402

from pyspark.sql import SparkSession  # noqa: E402

spark = (
    SparkSession.builder.master("local[1]")
    .appName("task260-cross3")
    .config("spark.sql.shuffle.partitions", "4")
    .config("spark.ui.enabled", "false")
    .config("spark.sql.session.timeZone", "UTC")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")
major = spark.version[0]
(OUT / f"000-cross-spark{major}.txt").write_text(
    f"spark {spark.version}\n" + run_cross(spark) + "\n", encoding="utf-8"
)
print(f"wrote outputs/000-cross-spark{major}.txt (spark {spark.version})")
spark.stop()
