"""Run all pitfalls in one Spark session; write one output file per pitfall.

Usage: venv/py4/bin/python repro/run_all.py [--only ID ...] [--write-wrappers]
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import duckdb  # noqa: E402
import sqlite3  # noqa: E402

from common import OUT, Ctx, write_pitfall  # noqa: E402
from pitfalls_core import PITFALLS as CORE  # noqa: E402
from pitfalls_more import PITFALLS as MORE  # noqa: E402


def build_ctx() -> tuple[Any, Ctx]:
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder.master("local[1]")
        .appName("task260-pitfalls")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    ctx = Ctx(spark=spark, duck=duckdb.connect(), sqlite=sqlite3.connect(":memory:"))
    return spark, ctx


def engine_line(ctx: Any) -> str:
    import platform

    return (
        f"python {platform.python_version()} | spark {ctx.spark.version} | "
        f"duckdb {duckdb.__version__} | sqlite {sqlite3.sqlite_version}"
    )


def write_wrappers(all_p: list[dict[str, Any]]) -> None:
    for p in all_p:
        name = f"{p['id']}-{p['slug']}.py"
        body = (
            f"#!/usr/bin/env python\n"
            f'"""Standalone runner for pitfall {p['id']}: {p['title'][:70]}\n'
            f"Run: ../venv/py4/bin/python {name}  (from repro/)\n"
            f'"""\n'
            f"import sys\n"
            f"from pathlib import Path\n"
            f"sys.path.insert(0, str(Path(__file__).parent))\n"
            f"import run_all\n"
            f"run_all.main(argv=[sys.argv[0], '--only', '{p['id']}'])\n"
        )
        (HERE / name).write_text(body, encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv[1:])
    all_p = CORE + MORE
    if "--write-wrappers" in argv:
        write_wrappers(all_p)
        print(f"wrote {len(all_p)} wrappers")
        argv = [a for a in argv if a != "--write-wrappers"]
    only = None
    if "--only" in argv:
        i = argv.index("--only")
        only = argv[i + 1]
    spark, ctx = build_ctx()
    el = engine_line(ctx)
    (OUT / "_versions.txt").write_text(el + "\n", encoding="utf-8")
    ok = err = 0
    for p in all_p:
        if only and p["id"] != only:
            continue
        try:
            body = p["fn"](ctx)
            write_pitfall(p, body, el)
            print(f"OK   {p['id']} {p['slug']}")
            ok += 1
        except Exception as e:  # noqa: BLE001 - record and continue with the rest
            msg = f"ERROR in fn: {type(e).__name__}: {str(e).splitlines()[0][:300]}"
            write_pitfall(p, msg, el)
            print(f"ERR  {p['id']} {p['slug']}: {msg[:150]}")
            err += 1
    if not only:
        from common import run_cross

        (OUT / f"000-cross-spark{spark.version[0]}.txt").write_text(
            f"spark {spark.version}, engine line: {el}\n" + run_cross(spark) + "\n", encoding="utf-8"
        )
    print(f"done: {ok} ok, {err} errored; outputs in {OUT}")
    spark.stop()


if __name__ == "__main__":
    main()
