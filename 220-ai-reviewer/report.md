Executed by: GLM-5.3 (account:zai-offpeak-idle-plan/GLM-5.3); effort: xh (default per instructions); ZCode idle subagent
Coordinator/run: coordinator model id: account:zai-offpeak-idle-plan/GLM-5.3; task 220-sql-spark-ai-reviewer-design; attempt 1; worker 8 of batch 3
Start: 2026-10-18T20:27:40+02:00  End: 2026-10-18T20:45:01+02:00

Assumption taken (no owner available): "MEASURE on at least 10 queries" was read as: run real local Spark
(pyspark 3.5.6, Java 17) on 12 self-authored cases and produce the four reading conditions as artifacts; the
"which condition reads best" table is filled by me and reported strictly as a descriptive self-audit (the task's
own completion checks demand this framing). BIRD/Snowflake/Databricks/Spark-Connect pages that 404'd are
recorded as not verified, not as findings.

# Result

1. Failure-mode taxonomy: failures.tsv (26 rows: id, mode, description, source, measured rate or honest label,
   deterministic vs reasoning mitigation). 14 sources verified by fetch 2026-10-18 with verbatim quotes
   (Spider 2.0, BIRD site, DIN-SQL, MAC-SQL, DAIL-SQL, Spark EXPLAIN docs, Substrait, Calcite, sqlglot README,
   Anthropic skills post, Codex/OpenAI skills page, plus own runs); folklore/unverified rows are labelled as
   such in the row (F15, F18, F21-F23, F25, F26). Own measurements ground F05-F12 and F16-F17.
2. Mitigations: mitigations.tsv (14 rows), each with evidence and a deterministic-script vs model-reasoning split;
   M01-M06, M12 are implemented as scripts in this results dir and validated (see below).
3. Intermediate representations: representations.md — layer table (SQL text -> parsed -> analyzed -> optimized ->
   physical -> whole-stage codegen -> UI/event log) built from the docs quote plus my own q01 EXPLAIN EXTENDED
   artifact; cross-engine IR table (Calcite, Substrait, sqlglot AST, Spark Connect, DataFrame API); plan formats
   (EXTENDED/COST/FORMATTED semantics from the fetched docs). The reading experiment: 12 cases (10 defects +
   2 controls, answer key separate at artifacts/answer-key.tsv), 4 conditions each, all artifacts on disk
   (artifacts/cases/qNN/{question,explain-extended,explain-formatted,explain-cost,compact,ast}.txt).
   Headline: SQL-only found ~7/10, SQL+plan and compact 9/10 (q05 skew and q08 data-format defects are in NO
   textual condition; skew showed only in the event log as max/median 17.1), AST adds nothing for defect-finding
   but powers the deterministic lints; one systematic false-claim temptation (broadcast advice without config,
   q06) and one noisy WARN (200-partition, fired on 11/12 incl. control) are documented.
4. Skills: design.md (format research summary + skill set + build order + benchmark-testing + privacy) and
   drafts/ with four DRAFT skills: sql-pitfall-lint (lint_sql.py), spark-plan-review (compact_plan.py),
   spark-skew-check (eventlog_summary.py), sql-review-report (skeleton + redaction draft). The compact-plan
   script required by the task exists and is validated: scripts/test_compact.py = 13/13 PASS (joins, filters,
   estimates, partitioning, warning-bearing nodes kept; elision explicit; unknown node types listed, never
   dropped; q01 4435 -> 3456 chars). Scripts smoke-tested again from their draft locations.
5. decision.md (retro-prep format): question, 14-row evidence table, 3 options, recommendation (deterministic-first
   pipeline in order lint -> plan -> skew -> report; medium-high confidence, low on generalisation), what would
   change my mind, what only the owner can decide.
6. Tooling hygiene: everything ran in results-dir venv (uv, Python 3.11); all 6 scripts pass
   `mypy --strict --ignore-missing-imports` (the ignore covers only untyped pyspark/sqlglot imports;
   Success: no issues found in 6 source files). Everything is pure Python/pyspark: Windows+Docker compatible,
   nothing WSL-only, nothing posted, no credentials used.

## Step -> evidence map (completion check)

- Part 1 taxonomy with >=25 sources: PARTIAL — failures.tsv has 26 evidence-bearing rows, but only 14 sources
  are fetch-verified with quotes; 10+ rows are labelled folklore/not-verified rather than padded with invented
  citations. Shortfall reported, not hidden.
- Part 1 deterministic-vs-reasoning split: DONE (failures.tsv last two columns, mitigations.tsv).
- Part 2 layers + IRs + plan formats: DONE (representations.md sections 1-2; Spark Connect protobuf row marked
  NOT verified - docs page 404).
- Part 2 measurement >=10 queries, 4 conditions: DONE as self-audit (12 cases; contamination, presentation
  order and control-case results stated in representations.md section 3).
- Part 3 skill-format research + skill set + drafts + tested compactor script: DONE (design.md, drafts/, 13/13
  fixture test; skills reference the verified cases and their blind spots).
- Stop condition ("deliverables exist, every row has its evidence; report what you could not verify"): met with
  the shortfalls listed in handoff.md (Unverified / Not searched).
