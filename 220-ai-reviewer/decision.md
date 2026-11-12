# Decision — task 220 (retro-prep format)

## 1. Question

Which deterministic helpers and which query representation should the bank's SQL/Spark AI-review skills build
on first, in which order, and what evidence would show a skill actually helps?

## 2. Evidence table (source or command with output; fetch/run date 2026-10-18)

| # | claim | source / command | quote or output |
|---|---|---|---|
| E1 | frontier agents fail ~4 in 5 real enterprise text-to-SQL workflow tasks | arxiv.org/abs/2411.07763 (fetched) | "successfully solves only 21.3% of the tasks" vs "91.2% on Spider 1.0" |
| E2 | humans 92.96 vs best LLMs far below on BIRD; even Lite: o3-mini 44.81% | bird-bench.github.io (fetched) | "Human Performance ... 92.96"; "SOTA model o3-mini only achieves 44.81% Success Rate" |
| E3 | decomposition/schema focus lifts accuracy ~10% | arxiv.org/abs/2304.11015 (fetched) | "improves their simple few-shot performance by roughly 10%" |
| E4 | degradation concentrates on huge schemas / multi-step | arxiv.org/abs/2312.11242 (fetched) | "significant performance degradation on 'huge' databases and complex user questions" |
| E5 | EXPLAIN EXTENDED exposes all four plan layers; COST adds statistics | spark.apache.org/docs/latest/sql-ref-syntax-qry-explain.html (fetched) | "Generates parsed logical plan, analyzed logical plan, optimized logical plan and physical plan" |
| E6 | sqlglot: parse/transpile 30+ dialects, canonical AST optimizer | github.com/tobymao/sqlglot README (fetched) | "no-dependency SQL parser, transpiler, optimizer"; "over 30 dialects" |
| E7 | own: plan text turns invisible SQL defects explicit | artifacts/cases/q01 vs q02; compact digest WARN (run) | q01 physical plan "CartesianProduct"; q02 "SortMergeJoin ... Inner" after isnotnull pushdown |
| E8 | own: skew invisible in every textual IR, visible in event log | eventlog_summary.py on artifacts/eventlog (run) | "7 200 15 21 256 17.1 SKEW" |
| E9 | own: compact digest keeps the signal | test_compact.py (run) | 13/13 PASS; q01 4435->3456 chars |
| E10 | own: lint catches the 4 classic NULL/cartesian traps, silent on 2 semantic ones | lint_sql.py on q01-q04/q07/q10 (run) | fired q01,q02,q03,q04; silent q07,q10 |
| E11 | own: plan conditions invite one systematic false claim (broadcast advice without config) | q06 self-audit (run) | threshold=-1 caused the SMJ; SQL-only sees nothing |
| E12 | own: compact WARN has a noise mode | WARN grep (run) | 200-partition WARN fired in 11/12 cases incl. clean control q09 |
| E13 | skill format: progressive disclosure, scripts for deterministic behavior | anthropic.com engineering post; learn.chatgpt.com/docs/build-skills (fetched) | "just enough information ... without loading all of it into context"; "Prefer instructions over scripts unless you need deterministic behavior" |
| E14 | IR landscape: Calcite relational algebra; Substrait cross-engine; sqlglot AST | calcite.apache.org, substrait.io (fetched) | see representations.md table |

## 3. Options

A. Deterministic-first pipeline (lint -> plan digest -> event-log stats -> report), prose skills minimal.
   Cost: build 3 small scripts (already drafted and tested here); Benefit: model reasons only about the unusual;
   Risk: lint false positives and WARN noise need curation (E12).
B. Plan-only skill: give the model full EXPLAIN EXTENDED, no scripts.
   Cost: cheapest; Benefit: plans already carry most defects (E7); Risk: context bloat on 1000-column schemas
   (E1/E4), no skew detection (E8), raw ids are noise.
C. Reasoning-only: a pitfall checklist in prose, no scripts.
   Cost: none; Benefit: portable; Risk: re-does what a parser does better; unverified advice slips in (E11).

## 4. Recommendation

Option A, built in order 1 sql-pitfall-lint, 2 spark-plan-review, 3 spark-skew-check, 4 sql-review-report
(evidence E10, E7/E9, E8, E13). Confidence: medium-high on the order and the representations (own measurements,
E7-E12, plus E3/E4 for decomposition); low-to-medium on generalisation beyond these 12 self-authored cases -
single model, self-audit, contaminated by construction (stated in representations.md).
What would change my mind: (a) on new blind cases the lint false-positive rate above ~30% (would demote lint to
advisory); (b) plan digest showing no finding-rate difference vs SQL-only on blind cases (would kill skill 2);
(c) the bank's Spark being Spark-Connect-only (protobuf plans replace EXPLAIN capture). How many cases the rule
rests on: 12 authored cases + 2 controls, one model, one run - treat every rate as illustrative, not measured
capability.

Evidence a skill helps (needed before trusting it): blind case sets (cases the reviewing session never saw),
fixed question per condition, findings scored against a separate key, false-positive count on controls, and a
before/after on real bank queries with the owner scoring usefulness. Nothing weaker than that.

## 5. Only the owner can decide

- Whether event logs can be exported from the bank platform to the review machine (skill 3 lives or dies).
- The redaction/egress rule (nothing leaves without approval; approve the redaction draft).
- Which models (Opus/Sonnet/GPT) run which skill, and on-prem vs cloud assumptions for the pipeline.
- Not verified by me: vendor AI-assistant behaviors (Databricks/Snowflake docs 404 this run), Spark Connect
  protobuf details, full-paper failure taxonomies (abstract-level quotes only). See handoff.md Unverified.

## Errata 2026-10-31 (2026-10-18 code review, approved by the owner)

The text above is preserved. Where it conflicts, this section wins.

- "12 authored cases + 2 controls" is wrong: the total is 12, being 10 defects + 2 controls. 7/10 versus 9/10 is descriptive, not a measured causal improvement.
