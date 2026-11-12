---
name: spark-plan-review
description: Use when reviewing Spark SQL or DataFrame queries for correctness or performance and a Spark EXPLAIN output (EXTENDED/COST/FORMATTED) is available or can be produced. Turns raw EXPLAIN text into a compact digest with warning lines, so the model reasons about the unusual parts instead of re-reading plan boilerplate. Not for writing new SQL from scratch.
---

# Spark plan review

## When to use
- Input is a query plus its EXPLAIN output (or access to a Spark session to produce one).
- Goal: find correctness defects or serious performance problems, or check a proposed change.

## Steps
1. Capture the plans (Docker: any pyspark 3.5/4.0 image; Windows hosts run this in the container):
   `python capture_explain.py query.sql` -> writes explain-extended/cost/formatted files next to it.
2. Digest: `python scripts/compact_plan.py <explain-file>` -> compact tree + WARNINGS + UNKNOWN lists.
3. Read the WARNINGS first; each names the plan line. Known kinds (validated 2026-10-18 on fixtures):
   cartesian product, nested-loop join, anti/semi join (NULL semantics), unpartitioned window,
   single-partition exchange, 200-partition default shuffle, python UDF.
4. UNKNOWN node types are listed, never dropped: look them up in the Spark version's docs before judging.
5. Compare optimized vs physical layers: a LEFT JOIN that became `Inner` + `isnotnull` in the optimized plan
   means a WHERE filter defeated the outer join (case F06 of the task-220 taxonomy).
6. Every finding must quote the exact plan line (or SQL line). No measurement -> no optimisation claim.

## Blind spots (verified, task 220 run 2026-10-18)
- Skew and actual sizes are NOT in the static plan (case q05: only the event log showed max/median 17.1).
  Use skill `spark-skew-check` when runtime data exists.
- Config artifacts: a SortMergeJoin may exist only because broadcast/AQE was disabled; record spark.sql.*
  settings together with the plan (case q06).
- EXPLAIN digest keeps column lists clipped to 3 with an explicit "...(N more cols elided)" marker; if the
  answer may hide in the elided columns, go back to the raw file.

## Privacy
Query text and plans never leave the machine unless the owner approves; see redaction note in
`sql-review-report`.
