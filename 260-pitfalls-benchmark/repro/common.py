"""Shared plumbing for task 260 pitfall repros.

Each pitfall is a dict: id, slug, title, category, engines, why, detect_static,
detect_test, source, fn(ctx)->str. Evidence rule: fn must print WRONG/RIGHT
lines computed by actually running the engine; never hardcode results.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
OUT.mkdir(exist_ok=True)

Pitfall = dict[str, Any]


class Ctx:
    """Engines handed to each pitfall function."""

    def __init__(self, spark: Any, duck: Any, sqlite: sqlite3.Connection) -> None:
        self.spark = spark
        self.duck = duck
        self.sqlite = sqlite


def rows(df: Any) -> list[Any]:
    return [tuple(r) for r in df.collect()]


def sql(spark: Any, q: str) -> list[Any]:
    return rows(spark.sql(q))


# (label, ansi_enabled, sql) — run on Spark 3 and Spark 4, diff the outputs.
CROSS_QUERIES: list[tuple[str, bool, str]] = [
    ("cast_str_int", False, "SELECT CAST('abc' AS INT) AS v"),
    ("cast_str_int", True, "SELECT CAST('abc' AS INT) AS v"),
    ("str_eq_int", False, "SELECT '10' = 10 AS v"),
    ("str_eq_int", True, "SELECT '10' = 10 AS v"),
    ("div_zero", False, "SELECT 1 / 0 AS v"),
    ("div_zero", True, "SELECT 1 / 0 AS v"),
    ("try_divide", False, "SELECT try_divide(1, 0) AS v"),
    ("int_overflow", False, "SELECT 2147483647 + 1 AS v"),
    ("int_overflow", True, "SELECT 2147483647 + 1 AS v"),
    ("long_overflow", False, "SELECT 9223372036854775807 + 1 AS v"),
    ("long_overflow", True, "SELECT 9223372036854775807 + 1 AS v"),
    ("cast_bad_date", False, "SELECT CAST('2026-02-30' AS DATE) AS v"),
    ("cast_inf", False, "SELECT CAST('inf' AS DOUBLE) AS v"),
    ("try_cast", False, "SELECT try_cast('abc' AS INT) AS v"),
]


def run_cross(spark: Any) -> str:
    """Run CROSS_QUERIES, return text block with result or first error line."""
    out: list[str] = [f"session_default_ansi={spark.conf.get('spark.sql.ansi.enabled')}"]
    for label, ansi, q in CROSS_QUERIES:
        spark.conf.set("spark.sql.ansi.enabled", "true" if ansi else "false")
        try:
            res = sql(spark, q)
            out.append(f"{label}\tansi={ansi}\tOK {res}")
        except Exception as e:  # noqa: BLE001 - record the engine error
            first = str(e).strip().splitlines()[0][:160]
            out.append(f"{label}\tansi={ansi}\tERR {first}")
    spark.conf.set("spark.sql.ansi.enabled", "false")
    return "\n".join(out)


def write_pitfall(p: Pitfall, body: str, engine_line: str) -> Path:
    name = f"{p['id']}-{p['slug']}.txt"
    text = "\n".join(
        [
            f"# {p['id']} {p['title']}",
            f"category: {p['category']}",
            f"engines: {p['engines']}",
            f"why: {p['why']}",
            f"detect_static: {p['detect_static']}",
            f"detect_test: {p['detect_test']}",
            f"source: {p['source']}",
            f"run: {engine_line}",
            "",
            body,
            "",
        ]
    )
    path = OUT / name
    path.write_text(text, encoding="utf-8")
    return path


Runner: Callable[[Ctx], str] = Callable[[Ctx], str]
