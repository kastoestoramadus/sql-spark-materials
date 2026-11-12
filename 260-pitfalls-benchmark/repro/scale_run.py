"""Local scale-trend experiment (Part 2): fact-dim join + groupBy at scale 1/10/100.

Measures wall time, total shuffle bytes written (from the Spark event log) and
plan shape (exchange count). LOCAL OBSERVATIONS ONLY - no cluster extrapolation.

Run: ../venv/py4/bin/python scale_run.py   (from repro/)
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EV = HERE / "outputs" / "events"

from pyspark.sql import SparkSession  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

SIZES = [10_000, 100_000, 1_000_000]  # scale 1, 10, 100


def shuffle_bytes(evdir: Path) -> int:
    total = 0
    for f in evdir.glob("*"):
        if not f.is_file():
            continue
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            acc = ev.get("Task Metrics", {}).get("Shuffle Write Metrics", {})
            total += int(acc.get("Shuffle Bytes Written", 0))
    return total


def main() -> None:
    shutil.rmtree(EV, ignore_errors=True)
    EV.mkdir(parents=True)
    spark = (
        SparkSession.builder.master("local[2]").appName("task260-scale")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.ui.enabled", "false")
        .config("spark.eventLog.enabled", "true")
        .config("spark.eventLog.dir", EV.as_uri())
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    print("scale\trows\twall_ms\tshuffle_bytes\texchanges")
    for i, n in enumerate(SIZES):
        evsub = EV / f"run{i}"
        evsub.mkdir()
        # rotate to a fresh event log file per size
        spark.sparkContext.setLocalProperty("spark.job.description", f"scale-{n}")
        dim = spark.range(0, 1000).select(F.col("id").alias("k"), (F.col("id") % 7).alias("grp"))
        # skewed key: pow(uniform,3) concentrates near 0 -> hot keys preserved at every scale
        fact = (
            spark.range(0, n)
            .select(
                F.floor(F.pow(F.rand(seed=7), 3.0) * 1000).cast("int").alias("k"),
                (F.col("id") % 100).alias("bucket"),
                (F.col("id") % 13).alias("amt"),
            )
        )
        t0 = time.perf_counter()
        plan = spark.sql(
            "SELECT d.grp, SUM(f.amt) s, COUNT(*) c FROM {f} f JOIN {d} d ON f.k = d.k GROUP BY d.grp ORDER BY d.grp".format(
                f=fact.createOrReplaceTempView("fact") or "fact", d=dim.createOrReplaceTempView("dim") or "dim"
            )
        )
        res = plan.collect()
        wall = (time.perf_counter() - t0) * 1000
        evsub.mkdir(exist_ok=True)
        # move finished in-progress file into run dir
        for f in EV.glob("in-progress.*"):
            shutil.move(str(f), str(evsub / f.name))
        n_ex = sum("Exchange" in l for l in plan._jdf.queryExecution().executedPlan().toString().splitlines())
        print(f"{n // SIZES[0]}\t{n}\t{wall:.0f}\t{shuffle_bytes(evsub)}\t{n_ex}\trows_out={len(res)}")
    spark.stop()


if __name__ == "__main__":
    main()
