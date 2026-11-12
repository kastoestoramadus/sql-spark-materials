#!/usr/bin/env python
"""Fixture validation for compact_plan.py: joins, filters, estimates, partitioning and
warning-bearing nodes must survive compaction; unknown nodes must be listed, not dropped."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
CASES = R / "artifacts" / "cases"


def compact(case: str, which: str = "explain-extended.txt") -> str:
    out = subprocess.run([sys.executable, str(R / "scripts" / "compact_plan.py"), str(CASES / case / which)],
                         capture_output=True, text=True, check=True)
    return out.stdout


def main() -> int:
    checks: list[tuple[str, bool]] = []

    def want(label: str, cond: bool) -> None:
        checks.append((label, cond))

    c01 = compact("q01")
    want("q01 cartesian node kept", "CartesianProduct" in c01)
    want("q01 cartesian WARN", "cartesian product" in c01)
    want("q01 equi join keys kept", "SortMergeJoin [region], [country], Inner" in c01)
    c02 = compact("q02")
    want("q02 join type kept (LEFT silently became Inner)", "SortMergeJoin [customer_id], [customer_id], Inner" in c02)
    want("q02 pushed null filter kept", "isnotnull(customer_id)" in c02)
    c05 = compact("q05")
    want("q05 join kept", "SortMergeJoin" in c05)
    want("q05 pushed filters kept", "PushedFilters: [IsNotNull(region)]" in c05 or "IsNotNull(region)" in c05)
    c05c = compact("q05", "explain-cost.txt")
    want("q05 size estimates kept in cost digest", ("rows=" in c05c) or ("sizeInBytes" in c05c) or ("Statistics" in c05c))
    c07 = compact("q07")
    want("q07 unpartitioned window WARN", "unpartitioned window" in c07)
    want("q07 single-partition exchange WARN", "single-partition exchange" in c07)
    c12 = compact("q12")
    want("q12 exchange partitioning kept", "hashpartitioning(region" in c12)
    want("q12 200-partition WARN", "200 shuffle partitions" in c12)
    sizes = {c: len((CASES / c / "explain-extended.txt").read_text()) for c in ["q01", "q10"]}
    digests = {c: len(compact(c)) for c in ["q01", "q10"]}
    want("digest smaller than input", all(digests[c] < sizes[c] for c in sizes))

    import compact_plan
    want("headerless physical plan preserved", "BroadcastNestedLoopJoin" in compact_plan.parse("BroadcastNestedLoopJoin BuildRight, Inner"))
    long_scan = "== Physical Plan ==\nFileScan parquet " + "padding " * 40 + "PushedFilters: [IsNotNull(critical)]"
    want("late pushed filters preserved", "IsNotNull(critical)" in compact_plan.parse(long_scan))
    want("unknown node explicitly listed", "UNKNOWN: Physical Plan: MysteryNode" in compact_plan.parse("== Physical Plan ==\nMysteryNode critical"))
    failed = [label for label, ok in checks if not ok]
    for label, ok in checks:
        print(("PASS " if ok else "FAIL ") + label)
    print(f"input chars {sizes} -> digest chars {digests}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
