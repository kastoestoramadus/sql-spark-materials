# Task 220 Part 2: intermediate representations of a SQL query

Own measurements run 2026-10-18, pyspark 3.5.6 (local[2], Java 17 Corretto), sqlglot 30.23.0, on Linux/WSL2;
every command and artifact lives in this results dir (`artifacts/`, `scripts/`). All scripts are pure Python or
pyspark and run unchanged on Windows with Docker (pyspark image or `uv venv` inside a container); nothing here
needs WSL specifically — WSL only happened to be the worker's host.

## 1. The layers a query goes through (Spark Catalyst)

Evidence: `artifacts/cases/q01/explain-extended.txt` contains all four sections verbatim; the docs
(https://spark.apache.org/docs/latest/sql-ref-syntax-qry-explain.html, fetched 2026-10-18) define the modes:

> "EXTENDED: Generates parsed logical plan, analyzed logical plan, optimized logical plan and physical plan."

| layer | what it is | contains | lost / added vs SQL text | stability | size/readability |
|---|---|---|---|---|---|
| SQL text | surface syntax | dialect sugar, hints, comments; NOTHING about tables/columns being real | the ground truth for intent; comments/hints lost later | n/a | what the author wrote |
| Parsed logical plan (unresolved) | parser AST | structure with `'UnresolvedRelation`, `'UnresolvedAttribute` (q01 line 7: `'UnresolvedRelation [orders], [], false`) | added: nothing; lost: comments | unstable across versions (internal) | moderate; same shape as SQL |
| Analyzed logical plan | resolved by catalog | real attributes with ids `amount#145`, types in output header | ADDED: resolution decisions (which table each column came from) — this is where hallucinated columns die | ids (`#145`) unstable per session | verbose; ids are noise for a reader |
| Optimized logical plan | Catalyst rule output | predicate pushdown (`Filter isnotnull(region)`), projection pruning, join-type conversion | ADDED: what the optimizer DECIDED (q02: my LEFT JOIN is optimized to `Join Inner` + `isnotnull(customer_id)`); LOST: the author's declared join type! | rules change across versions | the most information-dense layer for a reviewer |
| Physical plan | strategies applied | concrete operators: `SortMergeJoin [region], [country], Inner`, `Exchange hashpartitioning(region, 200)`, `FileScan ... PushedFilters: [IsNotNull(region), EqualTo(priority,HIGH)]`, `*(n)` whole-stage codegen markers | ADDED: shuffle/broadcast choices, partition counts, pushed filters; LOST: nothing above | operator names fairly stable; strings not an API | ~1-4 KB per query (own q01: 4435 chars) |
| Whole-stage codegen | Janino-compiled JVM bytecode of fused operators | only the `*(n)` markers survive in text; the code is viewable via `EXPLAIN CODEGEN` | ADDED: fused operator code; LOST: everything textual | fragile by design (internal) | not for a reviewer; marker presence is enough |
| Spark UI / event log | runtime truth | per-operator metrics, per-task times; event log JSON has `SparkListenerSQLExecutionStart` with `physicalPlanDescription` | ADDED: actual row counts, spill, skew (own run: 16 SQL executions in the log) | event-log JSON schema evolves between minors | large (own log: 2.8 MB for 9 stages); must be summarised |

Quote (docs, fetched 2026-10-18): "COST: If plan node statistics are available, generates a logical plan and the
statistics." / "FORMATTED: Generates two sections: a physical plan outline and node details."

## 2. Cross-engine intermediate representations

| IR | what it contains (quote) | lost/added vs SQL | stability | fit for an AI reviewer |
|---|---|---|---|---|
| Apache Calcite relational algebra | "Industry-standard SQL parser, validator and JDBC driver"; "Represent your query in relational algebra, transform using planning rules" (calcite.apache.org fetched 2026-10-18) | adds full resolution + algebra; loses dialect surface | mature, versioned | good but JVM-bound; no out-of-the-box Spark physical info |
| Substrait | "a well-defined, cross-language specification for data compute operations"; "Submit a plan to different execution engines ... and get a consistent interpretation" (substrait.io fetched 2026-10-18) | engine-neutral plan; loses engine-specific decisions | spec still evolving | promising future interchange; not yet native to Spark SQL review |
| SQLGlot AST | "no-dependency SQL parser, transpiler, optimizer"; "over 30 dialects"; "rewrite queries into an 'optimized' form ... new canonical AST" (README fetched 2026-10-18) | keeps everything in the text, adds canonical form; no catalog, no sizes, no physical layer | very active project; AST repr format changed across versions (own note: `.rep()` absent in 30.23.0) | best cheap deterministic layer: parse, lint, transpile, diff |
| Spark Connect plan | the client/server protocol serialises the *logical* plan as protobuf (docs page spark-connect-protocol 404 this run — NOT verified, see handoff) | DataFrame ops travel as proto, SQL text never parsed server-side | proto schema versioned with Spark | relevant at the bank only if Spark Connect is in use; otherwise n/a |
| DataFrame API | programmatic plan construction (df.join(...)) | the "SQL" the model sees is code; plan identical after analysis | stable-ish API | alternative input surface: models read code fluently; same downstream layers |
| EXPLAIN FORMATTED/COST/EXTENDED | see table above | mode chooses depth | operator names stable-ish | the workhorse for review; compact via script |

## 3. Reading experiment: which representation does the reviewer (me) read best

METHOD. 12 own queries with 10 planted defects + 2 clean controls (answer key written BEFORE reading:
`artifacts/answer-key.tsv`; reviewer inputs in `artifacts/cases/`, key kept separate). Conditions per case:
(a) SQL only, (b) SQL + full EXPLAIN EXTENDED, (c) SQL + compact digest (`scripts/compact_plan.py` output),
(d) SQL + sqlglot AST (`repr()`). Question in every condition: "find the defect (correctness or serious
performance problem)".

SELF-AUDIT (required framing): I authored the cases and the answer key, so this is NOT a blinded or independent
comparison; it is a descriptive self-audit by one model (GLM-5.3) with prior exposure, in fixed order q01..q12,
SQL condition read first each time. No causal claim about model quality follows from it. The useful content is
WHICH ARTIFACT carries the signal, not how good the model is.

| case | defect (answer key) | SQL only | SQL+plan | compact | AST | notes / false claims |
|---|---|---|---|---|---|---|
| q01 | cartesian (ON t.priority='HIGH') | findable but easy to miss | FOUND (CartesianProduct) | FOUND + WARN names it | findable | plan condition strictly better |
| q02 | LEFT JOIN defeated by WHERE | found with care | FOUND fast (`SortMergeJoin ... Inner` + isnotnull) | FOUND (join line kept) | found | plan CONFIRMS the conversion |
| q03 | NOT IN nullable | found (classic pattern) | found; null-aware anti-join harder to read than SQL | WARN flags anti-join NULL semantics | found | SQL knowledge dominates here |
| q04 | != drops NULLs | found | found; isnotnull(status) visible | found | found | — |
| q05 | 80% skew on region | NOT found | NOT found | NOT found | NOT found | only event log shows it: stage 7 max/median 17.1 |
| q06 | none (SMJ caused by config threshold=-1) | no signal | temptation to claim "should broadcast" = FALSE CLAIM unless config known | same temptation | no signal | config must ship with plan (M12) |
| q07 | unpartitioned window | found (needs perf expertise) | FOUND obvious (Exchange SinglePartition) | FOUND + WARN | found | plan makes it obvious |
| q08 | to_date format mismatch | "verify format" only (data unknown) | same | same | same | needs a data sample or format contract |
| q09 | CONTROL (clean) | clean | clean | WARN noise: 200-partition line fired (not a defect here) | clean | compact false-positive WARN |
| q10 | join fanout double count | found with arithmetic care | found; plan adds little | found | found | SQL-level reasoning |
| q11 | CONTROL (clean) | clean | clean | clean | clean | — |
| q12 | 200 shuffle partitions, tiny data | NOT found | FOUND (Exchange ... 200) | FOUND + WARN | NOT found | plan-only finding |

Counts (10 defect cases): SQL only ~7/10 found (2 soft), SQL+plan 9/10 (q05, q08 unfindable in any text
condition), compact 9/10 with two automatic WARN hits and one false-positive WARN pattern (the 200-partition
WARN fired in 11/12 cases including the clean control — precise only with size context), AST 7/10 (adds nothing
over SQL for defects; value is parse/lint/transpile). False claims: one systematic temptation (q06 broadcast
advice without config) present in both plan conditions; controls stayed clean except the compact WARN noise.
One model, small sample, self-audit — as stated.

Digest cost: q01 4435 -> 3456 chars (78%); the larger the schema (bank: 1000+ columns, cf. F01), the larger the
saving, because column lists and paths are what grow.

## 4. What this says for the bank engagement

- The optimized/physical plan is the layer where SQL-text defects become undeniable (q01, q02, q07, q12) — ship
  EXPLAIN EXTENDED for every query under review, digested by `compact_plan.py`.
- No textual IR shows skew (q05): pair plans with an event-log or metrics step (`eventlog_summary.py`).
- The AST (sqlglot) is the cheap gate: parse errors, dialect pinning, NULL/cartesian lints before any model
  reading (`lint_sql.py`).
- Statistics (COST mode) belong in context when physical-design advice is asked for (F14/M04), and the spark
  config must travel with the plan or the model invents config-caused "defects" (q06).
