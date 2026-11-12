"""Per-size scale runner (each size = own Spark session, uncompressed event log).

Usage: scale_run2.py <rows>            -> writes outputs/scale-<rows>.json
       scale_run2.py report            -> prints TSV from all scale-*.json
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"


def one(n: int) -> None:
    ev = OUT / f"events-{n}"
    shutil.rmtree(ev, ignore_errors=True)
    ev.mkdir(parents=True)
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F

    spark = (
        SparkSession.builder.master("local[2]").appName(f"task260-scale-{n}")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.ui.enabled", "false")
        .config("spark.eventLog.enabled", "true")
        .config("spark.eventLog.dir", ev.as_uri())
        .config("spark.eventLog.compress", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    dim = spark.range(0, 1000).select(F.col("id").alias("k"), (F.col("id") % 7).alias("grp"))
    fact = (
        spark.range(0, n)
        .select(
            F.floor(F.pow(F.rand(seed=7), 3.0) * 1000).cast("int").alias("k"),
            (F.col("id") % 100).alias("bucket"),
            (F.col("id") % 13).alias("amt"),
        )
    )
    fact.createOrReplaceTempView("fact")
    dim.createOrReplaceTempView("dim")
    df = spark.sql("SELECT d.grp, SUM(f.amt) s, COUNT(*) c FROM fact f JOIN dim d ON f.k = d.k "
                   "GROUP BY d.grp ORDER BY d.grp")
    t0 = time.perf_counter()
    res = df.collect()
    wall_ms = (time.perf_counter() - t0) * 1000
    exchanges = sum("Exchange" in l for l in df._jdf.queryExecution().executedPlan().toString().splitlines())
    spark.stop()
    bytes_written = 0
    for f in ev.rglob("events_*"):
        if f.is_file() and not str(f).endswith(".crc"):
            for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    evj: dict[str, Any] = json.loads(line)
                except json.JSONDecodeError:
                    continue
                m = evj.get("Task Metrics", {})
                sw = m.get("Shuffle Write Metrics", {})
                bytes_written += int(sw.get("Shuffle Bytes Written", 0))
    (OUT / f"scale-{n}.json").write_text(
        json.dumps({"rows": n, "wall_ms": round(wall_ms), "shuffle_bytes": bytes_written,
                    "exchanges": exchanges, "rows_out": len(res)}), encoding="utf-8")
    print(f"scale-{n}: {wall_ms:.0f} ms, {bytes_written} shuffle bytes, {exchanges} exchanges")


def report() -> None:
    print("scale\trows\twall_ms\tshuffle_bytes\texchanges")
    for f in sorted(OUT.glob("scale-*.json"), key=lambda p: int(p.stem.split("-")[1])):
        d = json.loads(f.read_text(encoding="utf-8"))
        print(f"{d['rows'] // 10000}\t{d['rows']}\t{d['wall_ms']}\t{d['shuffle_bytes']}\t{d['exchanges']}")


if __name__ == "__main__":
    if sys.argv[1] == "report":
        report()
    else:
        one(int(sys.argv[1]))
