# Handoff — task 220-sql-spark-ai-reviewer-design, attempt 1

## Done
- report.md (identity block + step->evidence map), failures.tsv (26 rows), mitigations.tsv (14 rows),
  representations.md (layers, IR table, 12-case x 4-condition reading experiment), design.md, decision.md
  (retro-prep format), commands.log, progress.md, checkpoint.md.
- Own measurement pipeline, all inside the results dir (venv: uv, Python 3.11, pyspark 3.5.6, sqlglot 30.23.0):
  - scripts/make_plans.py — builds 5 tables incl. planted 80%-single-key skew, runs 12 review cases
    (10 defects + 2 controls), writes question/explain-extended/explain-formatted/explain-cost per case plus a
    Spark event log (artifacts/eventlog, 2.8 MB). Answer key kept separate: artifacts/answer-key.tsv.
  - scripts/make_conditions.py — writes compact.txt (compact_plan.py digest) and ast.txt (sqlglot repr) per case.
  - scripts/compact_plan.py — THE required compactor; validated by scripts/test_compact.py: 13/13 PASS
    (cartesian, join-type conversion, pushed filters, size estimates, partitioning, window warnings kept;
    elision explicit; unknown node types listed).
  - scripts/lint_sql.py — deterministic pitfall linter (fired q01 no-equi-join, q02 outer-join-defeated,
    q03 not-in-subquery, q04 neq-null; silent on q07/q10).
  - scripts/eventlog_summary.py — per-stage task stats; flagged planted skew: "7 200 15 21 256 17.1 SKEW".
  - All 6 scripts pass `mypy --strict --ignore-missing-imports` (ignore covers untyped pyspark/sqlglot only).
- drafts/ — 4 DRAFT skills with scripts copied in and smoke-tested from the draft paths:
  sql-pitfall-lint, spark-plan-review, spark-skew-check, sql-review-report.
- 14 sources fetch-verified 2026-10-18 with verbatim quotes (listed in failures.tsv / decision.md).
- No repository files touched, nothing pushed/posted, no credentials; writes only in this results dir.

## Not done
- 25 fetch-verified sources: only 14 verified; the remaining rows in failures.tsv are labelled folklore /
  not-verified instead of being padded with unverified citations (audit rule).
- Spark Connect protobuf row: docs page 404; represented as NOT verified in representations.md.
- Vendor AI-assistant behaviors (Databricks Assistant, Snowflake Copilot, Amazon Q): docs 404; no claims made.
- Full-paper failure taxonomies (Spider 2.0 breakdown, DIN-SQL error table): abstract-level quotes only.
- Reading experiment independence: impossible by design (same worker authored the cases); reported as a
  descriptive self-audit, per the task's own completion checks. Not fixable by starting another model (forbidden).

## Proposals needing a decision
- Redaction script (M13/F24): implement a literal/identifier-redaction regex tool before any bank query leaves
  a machine. Risk: false sense of safety (jargon names); recommendation: owner reviews the redacted diff rule.
- Skill build order (decision.md): lint -> plan digest -> skew -> report. Risk if reversed: reasoning errors the
  deterministic layer already prevents.
- Grow the benchmark: every real bank review adds a case + control to artifacts/; keep answer key separate.
  Recommendation: adopt before the engagement starts.

## Ready-made texts
- None needed (no PR, no issue; results-dir task). PR-body template rule acknowledged for future use.

## Verification (commands + outputs)
- test_compact.py: 13x PASS + "input chars {'q01': 4435, 'q10': 4019} -> digest {3456, 3363}".
- lint_sql.py on q01: "HIGH no-equi-join ..."; q02: "HIGH outer-join-defeated ..."; q03: "HIGH not-in-subquery".
- eventlog_summary.py: stage row "7 200 15 21 256 17.1" with SKEW; "sql executions with plan in log: 16".
- mypy: "Success: no issues found in 6 source files".
- make_conditions.py: "ast dumps: 12, compact dumps: 12".

## Unverified
- Not searched: Hacker News/practitioner blogs on AI query tuning; Query balloons/vendor AI-assistant docs
  (404s above); test-suite/execution-equivalence papers (only methodology cited via benchmark design);
  Spark Connect protobuf spec; SQLancer/differential-testing primary pages; BIRD full-paper error analysis;
  any bank-internal data (never sought, per brief).
- Self-audit contamination: all "which condition reads best" numbers are one model, self-authored cases,
  fixed order (q01..q12, SQL condition first); treat as illustrative, as stated in representations.md.
- Prompt injection: none encountered in fetched pages (no page attempted to instruct).
