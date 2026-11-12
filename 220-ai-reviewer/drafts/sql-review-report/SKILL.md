---
name: sql-review-report
description: Use when the findings of a SQL/Spark review must be written up for engineers or management: enforces evidence-linked findings (every finding quotes a SQL line, plan line or metric), a findings/uncertainty split, measured before/after for optimisation claims, and a redaction pass before any content may leave the machine. Output is English Markdown. Not for running reviews itself - it formats and gates them.
---

# SQL review report

## When to use
- Findings exist from `sql-pitfall-lint`, `spark-plan-review`, `spark-skew-check` and must be communicated.

## Report skeleton (fill every heading or write "none")
1. Query under review (id, source, dialect, spark version, spark.sql.* settings that shape the plan).
2. Findings: each = severity, SQL/plan/metric evidence quoted verbatim, why it is a defect, suggested change.
3. NOT findings: what was checked and found clean (controls; keeps false positives visible).
4. Optimisation claims: before/after numbers from `spark-skew-check` runs; no numbers -> listed as
   "unverified suggestion", never as a finding.
5. Uncertainties: what only production data or the data owner can answer (nullability, formats, skew).

## Redaction before anything leaves the machine (draft, owner approves)
- Replace string/date literals with :str_1..n, numbers with :num_1..n, keep only: operator kinds, column
  counts, row counts, timings. Regex replace, then manual pass on table/column names (they can be internal
  jargon); a diff of row counts before/after redaction proves the query was not otherwise altered.
- Nothing leaves the machine without the owner's approval (bank data; task brief).

## Evidence rule (from the task-220 taxonomy)
A finding without a quote is an opinion; label it as such. Folklore has no place in findings.

## Privacy
The report is written locally; the redaction gate is the only path outward.
