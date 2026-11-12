#!/usr/bin/env python
"""Turn a Spark EXPLAIN output into a compact plan digest for an AI reviewer.

Reads a text file containing Spark EXPLAIN output (EXTENDED, COST, FORMATTED or
default physical plan). Emits, per section found:
  - the tree with node type, join keys/type, Exchange partitioning, PushedFilters,
    Window specs, Sort specs and size estimates kept; expression ids (#123),
    plan_ids, file paths and ReadSchema details dropped; long column lists cut
    with an explicit ellipsis so lost information stays visible;
  - a WARNINGS list for suspicious nodes (cartesian products, nested-loop joins,
    anti/semi joins, unpartitioned windows, 200-partition exchanges);
  - an UNKNOWN list naming node types not in the known vocabulary, so nothing is
    silently mangled.

Deterministic: same input, same output. No network, no Spark needed.
"""
from __future__ import annotations

import argparse
import re
import sys

KNOWN_NODES: frozenset[str] = frozenset({
    "Aggregate", "BatchEvalPython", "ArrowEvalPython", "BroadcastExchange", "BroadcastHashJoin",
    "BroadcastNestedLoopJoin", "CartesianProduct", "ColumnarToRow", "Exchange", "Expand", "Filter",
    "FileScan", "Generate", "HashAggregate", "InMemoryRelation", "InMemoryTableScan", "Join",
    "LocalTableScan", "ObjectHashAggregate", "Project", "Range", "RowToColumnar", "Scan",
    "Sort", "SortAggregate", "SortMergeJoin", "Subquery", "SubqueryAlias", "Window",
    "WindowGroupLimit", "WholeStageCodegen", "ShuffledHashJoin", "TakeOrderedAndProject",
})

RE_EXPR_ID = re.compile(r"#\d+L?")
RE_PLAN_ID = re.compile(r",?\s*\[plan_id=\d+\]")
RE_CODEGEN = re.compile(r"^\*\(\d+\)\s*")
RE_SCHEMA = re.compile(r"ReadSchema: struct<[^>]*>")
RE_LOCATION = re.compile(r"Location: InMemoryFileIndex\(\d+ paths\)\[[^\]]*\]")
RE_EXCHANGE = re.compile(r"(hashpartitioning|rangepartitioning|SinglePartition|RoundRobinPartitioning)\(([^)]*)\)")
RE_COLSLIST = re.compile(r"\[([^\]]{60,})\]")
WARN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("cartesian product (no equi-join condition)", re.compile(r"CartesianProduct")),
    ("nested-loop join (no equi-join condition)", re.compile(r"NestedLoopJoin")),
    ("anti/semi join - NULL semantics matter", re.compile(r"(LeftAnti|LeftSemi|RightAnti|RightSemi)")),
    ("unpartitioned window - every row in one partition/task", re.compile(r"^Window \[.*\], \[[^\]]*\]$")),
    ("single-partition exchange - all rows to one task", re.compile(r"Exchange SinglePartition")),
    ("default 200 shuffle partitions for a small shuffle", re.compile(r"hashpartitioning\([^)]*,\s*200\)")),
    ("python UDF breaks codegen (BatchEvalPython)", re.compile(r"BatchEvalPython|ArrowEvalPython")),
)
RE_TREE_CHARS = re.compile(r"^[:+\-\s]*")
RE_SCHEMA_LINE = re.compile(r"^[a-z_0-9]+: (string|decimal|bigint|long|int|date|boolean|double)")


def clip_lists(line: str, keep: int = 3) -> str:
    """Cut long bracketed column lists to `keep` entries plus an explicit ellipsis."""
    def _clip(m: re.Match[str]) -> str:
        items = [i.strip() for i in m.group(1).split(",")]
        shown = ", ".join(items[:keep])
        return f"[{shown}, ...({len(items) - keep} more cols elided)]"
    return RE_COLSLIST.sub(_clip, line)


def clean_line(line: str) -> str:
    line = RE_EXPR_ID.sub("", line)
    line = RE_PLAN_ID.sub("", line)
    line = RE_SCHEMA.sub("ReadSchema: <elided>", line)
    line = RE_LOCATION.sub("Location: <paths elided>", line)
    line = re.sub(r"spark_catalog\.default\.", "", line)
    line = clip_lists(line) if line.startswith("Project ") else line
    return re.sub(r",\s*,", ",", line)


def node_type(line: str) -> str:
    m = re.match(r"([A-Za-z]+)", line)
    return m.group(1) if m else "?"


def compact_section(title: str, body: list[tuple[int, str]], out: list[str], warnings: list[str], unknown: list[str]) -> None:
    out.append(f"== {title} ==")
    for depth, line in body:
        if RE_SCHEMA_LINE.match(line):
            continue  # analyzed-plan output header (column types), not a node
        bare = RE_CODEGEN.sub("", line)
        nt = node_type(bare)
        codegen = "" if not RE_CODEGEN.match(line) else "[wcg]"
        if nt not in KNOWN_NODES and nt not in ("?", "'Sort", "'Project", "'Join", "'Filter", "'Aggregate", "Relation", "'UnresolvedRelation"):
            unknown.append(f"{title}: {nt}")
        for label, pat in WARN_PATTERNS:
            if pat.search(line):
                warnings.append(f"{title}: {label} -> {bare[:90]}")
        out.append(f"{'  ' * depth}{'+- ' if depth else ''}{codegen}{clean_line(bare)}".rstrip())


def parse(text: str) -> str:
    out: list[str] = []
    warnings: list[str] = []
    unknown: list[str] = []
    section: str | None = None if any(x.startswith("== ") and x.endswith(" ==") for x in text.splitlines()) else "Physical Plan (headerless)"
    body: list[tuple[int, str]] = []
    for raw in text.splitlines():
        if raw.startswith("== ") and raw.endswith(" =="):
            if section and body:
                compact_section(section, body, out, warnings, unknown)
            section, body = raw.strip("= "), []
            continue
        if section and raw.strip():
            indent = len(raw) - len(raw.lstrip(" :"))
            content = RE_TREE_CHARS.sub("", raw.strip()).strip()
            body.append((max(0, (indent - 2)) // 3 if indent > 2 else 0, content))
    if section and body:
        compact_section(section, body, out, warnings, unknown)
    if warnings:
        out.append("== WARNINGS (suspicious nodes kept visible) ==")
        out.extend(f"  WARN: {w}" for w in dict.fromkeys(warnings))
    if unknown:
        out.append("== UNKNOWN NODE TYPES (not in vocabulary - inspect manually) ==")
        out.extend(f"  UNKNOWN: {u}" for u in dict.fromkeys(unknown))
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("infile", help="file with EXPLAIN output (EXTENDED/COST/FORMATTED/physical)")
    args = ap.parse_args()
    text = open(args.infile, encoding="utf-8").read()
    result = parse(text)
    sys.stdout.write(result)
    sys.stderr.write(f"[compact_plan] {len(text)} -> {len(result)} chars\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
