#!/usr/bin/env python
"""Summarise a Spark event log: per-stage task times and skew, plus SQL executions.

Reads the JSON-lines event log (spark.eventLog.enabled=true, .inprogress files fine),
prints one row per stage with n/median/p90/max task duration (ms) and a skew flag,
and lists SQL executions with their physical plan availability. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("eventlog", help="event log file or directory (one .json/.inprogress)")
    args = ap.parse_args()
    p = Path(args.eventlog)
    if p.is_dir():
        cands = sorted(x for x in p.iterdir() if x.is_file())
        if not cands:
            print("no event log file found")
            return 1
        if len(cands) != 1:
            raise ValueError("ambiguous event-log directory: select an explicit file")
        p = cands[0]
    task_ms: dict[int, list[int]] = defaultdict(list)
    stage_names: dict[int, str] = {}
    sql_execs: list[tuple[str, int]] = []
    with p.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                ev: dict[str, Any] = json.loads(line)
            except json.JSONDecodeError:
                continue
            et = ev.get("Event", "")
            if et.endswith("SparkListenerTaskEnd"):
                sid = int(ev.get("Stage ID", -1))
                m = ev.get("Task Executor Metrics") or {}
                ti = ev.get("Task Info") or {}
                dur = int(ti.get("Finish Time", 0)) - int(ti.get("Launch Time", 0))
                if dur > 0:
                    task_ms[sid].append(dur)
            elif et.endswith("SparkListenerStageSubmitted"):
                info = ev.get("Stage Info") or {}
                stage_names[int(info.get("Stage ID", -1))] = str(info.get("Stage Name", ""))[:70]
            elif et.endswith("SparkListenerSQLExecutionStart"):
                qid = ev.get("executionId", -1)
                has_plan = "physicalPlanDescription" in ev
                if has_plan:
                    sql_execs.append((str(ev.get("description", ""))[:60], qid))
    print("stage\ttasks\tmedian_ms\tp90_ms\tmax_ms\tskew(max/median)\tname")
    for sid, ts in sorted(task_ms.items()):
        ts.sort()
        med = statistics.median(ts)
        p90 = ts[int(len(ts) * 0.9) - 1] if len(ts) >= 10 else ts[-1]
        mx = ts[-1]
        ratio = mx / med if med else 0.0
        flag = "SKEW" if ratio > 5 and mx > 1000 else ""
        print(f"{sid}\t{len(ts)}\t{med:.0f}\t{p90}\t{mx}\t{ratio:.1f} {flag}\t{stage_names.get(sid, '')}")
    print(f"sql executions with plan in log: {len(sql_execs)} -> {sql_execs[:5]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
