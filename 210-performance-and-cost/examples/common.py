"""Shared helpers for the task-210 experiments.

Everything here is plain PySpark 3.5: it runs unchanged on Windows with Docker
(e.g. `docker run -it --rm -v %cd%:/w -w /w bitnami/spark:3.5 spark-submit
examples/e02_skew.py`), no WSL and no Linux-only tooling required.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

P = ParamSpec("P")
T = TypeVar("T")
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent
RUNS = RESULTS / "runs"
_EVENTLOG_APPS: dict[str, str] = {}


def make_spark(app: str, eventlog_name: str, **conf: str) -> "SparkSession":  # noqa: F821
    """SparkSession with an event log per experiment (measurement + UI evidence)."""
    from pyspark.sql import SparkSession

    # keep the UDF python worker on the same interpreter as the driver
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    log_dir = RUNS / eventlog_name / "eventlog"
    log_dir.mkdir(parents=True, exist_ok=True)
    b = (
        SparkSession.builder.master("local[4]")
        .appName(app)
        .config("spark.eventLog.enabled", "true")
        .config("spark.eventLog.dir", log_dir.as_uri())
        .config("spark.ui.enabled", "true")
    )
    for k, v in conf.items():
        b = b.config(k, v)
    spark = b.getOrCreate()
    _EVENTLOG_APPS[eventlog_name] = spark.sparkContext.applicationId
    return spark


def timed(fn: Callable[P, T], *a: P.args, **kw: P.kwargs) -> tuple[float, T]:
    """Run an action, return (seconds, value)."""
    t0 = time.perf_counter()
    v = fn(*a, **kw)
    return round(time.perf_counter() - t0, 2), v


def summarise_eventlog(eventlog_name: str) -> dict[str, Any]:
    """Aggregate the finished tasks of the run's event log.

    Returns per-stage: task count, max/p50/p75 runtime, shuffle bytes written,
    shuffle bytes read, input bytes and records. Reads the same JSON lines the
    Spark UI shows; it is the offline detection method for skew and shuffle.
    """
    import statistics

    d = RUNS / eventlog_name / "eventlog"
    candidates = [p for p in d.iterdir() if p.is_file() and not p.name.startswith(".")]
    app_id = _EVENTLOG_APPS.get(eventlog_name)
    if app_id is not None:
        candidates = [p for p in candidates if p.name.removesuffix(".inprogress") == app_id]
    if len(candidates) != 1:
        raise ValueError(f"expected one event log for {app_id or eventlog_name}; found {len(candidates)}")
    infile = candidates[0]
    stages: dict[int, dict[str, Any]] = {}
    jobs_done = 0
    with open(infile, encoding="utf-8") as fh:
        for line in fh:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            ev = e.get("Event")
            if ev == "SparkListenerTaskEnd":
                m = e["Task Metrics"]
                si = stages.setdefault(
                    e["Stage ID"],
                    {
                        "tasks": 0,
                        "max_ms": 0,
                        "durs": [],
                        "shuffle_write": 0,
                        "shuffle_read": 0,
                        "input_bytes": 0,
                        "input_records": 0,
                    },
                )
                si["tasks"] += 1
                dms = m.get("Executor Run Time", 0)
                si["durs"].append(dms)
                si["max_ms"] = max(si["max_ms"], dms)
                si["shuffle_write"] += m.get("Shuffle Write Metrics", {}).get("Shuffle Bytes Written", 0)
                si["shuffle_read"] += m.get("Shuffle Read Metrics", {}).get("Remote Bytes Read", 0) + m.get(
                    "Shuffle Read Metrics", {}
                ).get("Local Bytes Read", 0)
                si["input_bytes"] += m.get("Input Metrics", {}).get("Bytes Read", 0)
                si["input_records"] += m.get("Input Metrics", {}).get("Records Read", 0)
            elif ev == "SparkListenerJobEnd":
                jobs_done += 1
    out = {}
    for sid, si in stages.items():
        durs = sorted(si["durs"])
        out[sid] = {
            "tasks": si["tasks"],
            "max_task_ms": si["max_ms"],
            "p50_task_ms": durs[len(durs) // 2] if durs else 0,
            "p75_task_ms": durs[int(len(durs) * 0.75)] if durs else 0,
            "shuffle_write_bytes": si["shuffle_write"],
            "shuffle_read_bytes": si["shuffle_read"],
            "input_bytes": si["input_bytes"],
            "input_records": si["input_records"],
        }
    return {"jobs": jobs_done, "stages": out}


def save(eventlog_name: str, payload: dict[str, Any]) -> None:
    p = RUNS / eventlog_name / "summary.json"
    ev = summarise_eventlog(eventlog_name)
    payload["eventlog"] = {
        "jobs": ev["jobs"],
        "stages_total": len(ev["stages"]),
        "stages": ev["stages"],
        "path": str(RUNS / eventlog_name / "eventlog"),
    }
    p.write_text(json.dumps(payload, indent=2, default=str))
    print(f"[saved] {p}")
    for k, v in payload.items():
        if k != "eventlog":
            print(f"  {k}: {v}")
