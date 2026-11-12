# Decision: which three tools go into the agent's toolbox first (task 230)

## Question

Which three tools should an agent that analyses SQL/Spark jobs (performance, cost,
errors, optimisation) at a bank on Windows with Docker and no WSL get first?

## Evidence table (every row: source + date; local runs quoted in logs/)

| # | claim | source (fetch/run date 2026-10-18) |
|---|---|---|
| E1 | sqlglot transpiles spark<->postgres/databricks, parses errors with position, builds column lineage - pure pip | run: logs/sqlglot_probe.out, logs/sqlglot_lineage.out; PyPI 30.23.0 (2026-10-14), MIT |
| E2 | sqlfluff lints dialect `sparksql` and surfaces ambiguity/parse errors - pure pip | run: logs/sqlfluff_lint.out (21 findings); GitHub release 4.4.0 2026-10-02, MIT |
| E3 | sparkMeasure needs a Maven jar the wheel does not ship; with it, per-stage metrics are one python call | run: first attempt failed "jar is like not loaded" (logs/sparkmeasure.err 19:58), then worked with ch.cern.sparkmeasure:spark-measure_2.12:0.25 (Maven API latest check 2026-10-18); PyPI 0.28.0 2026-05-19, Apache-2.0 |
| E4 | DataFlint attaches to a driver with one Maven coord + one conf line and serves a UI tab | run: logs/dataflint.out ("DataFlint tab present: True"), logs/dataflint.err (jar from central); GitHub v0.9.9 2026-05-18, Apache-2.0, pushed 2026-08-20 |
| E5 | History Server reads the same event logs offline; both DataFlint and History Server are JVM-only, no Linux host needed beyond the JVM | run: logs/hs_stage17.json (API, app + stage summary); apache/spark docker tags 3.5.9/4.2.0 verified via hub.docker.com API |
| E6 | the planted skew (one task 25x median) and small files (60 x 1.8 KB) were visible to event-log-based tools and invisible to SQL-lint tools, as designed | run: logs/eventlog_truth.out, capability matrix in report.md |
| E7 | pydeequ 1.7.0 does not run against pyspark 3.5.9-py3.11 or 4.2.0 here (py4j iterableAsScalaIterable error) | run: logs/pydeequ.err, logs/pydeequ4.err; GitHub v1.7.0 2026-09-14 |
| E8 | soda-sparkdf/soda-core 4.27.0 licence field on PyPI says "Proprietary" | PyPI JSON 2026-10-13 (single source; not re-verified against their licence file) |
| E9 | Dr.Elephant dormant (pushed 2023-08-22), Sparklens last release 2020 | GitHub API 2026-10-18 |

## Options

A. sqlglot + sqlfluff + DataFlint - "SQL first, UI for humans".
   Cost: three pip/Maven installs; DataFlint needs Maven or a vendored jar.
   Benefit: covers static SQL analysis (dialect, lint, lineage) plus a visual
   performance UI; all Apache/MIT; all exercised here.
   Risk: DataFlint UI needs a human or screenshots; an agent gets more from raw metrics.

B. sqlglot + sparkMeasure + DataFlint - "agent-facing pipeline".
   Cost: same installs as A plus the sparkMeasure jar (vendored for offline).
   Benefit: sqlglot reads/writes the SQL, sparkMeasure yields machine-readable stage
   metrics per run (JSON/CSV), DataFlint gives the human-facing check; together they
   cover planted skew (E3/E6), SQL diagnostics (E1) and visual review (E4).
   Risk: no lint/style gate (sqlfluff missing); skew shows indirectly through
   sparkMeasure aggregates (E3) - the per-task spread needs the event-log JSON or
   History Server summary.

C. sqlglot + History Server + Great Expectations - "officials only".
   Cost: GE is a heavy install; Spark datasource needs a JVM; bank licence review
   likely fine (Apache-2.0).
   Benefit: everything official/vendor-supported; data quality included.
   Risk: GE not exercised here (no run); History Server UI is dated and its API is
   coarser than sparkMeasure's export; data-quality tools miss skew/small files by
   design (E6, matrix "unsupported" rows).

## Recommendation and confidence

Option B, with sqlfluff added as the cheap fourth when the owner wants a lint gate
(one pip line, no jar). Confidence: medium-high. It rests on the synthetic job only
(one planted skew, one small-files case - the "how many cases" answer: n=1 per
problem), plus 6 exercised installs on one machine (WSL2, not Windows-without-WSL).
What would change my mind: a Docker-enabled Windows run showing DataFlint or the
History Server container failing on the bank's mirrored registry; or the bank having
no Maven/vendor path at all (then swap DataFlint for sqlfluff and read event-log JSON
with the 40-line baseline script, which needed nothing but python).

## Only the owner can decide

- Whether Maven Central is reachable at the bank or jars must be pre-vendored
  (changes the install path, not the ranking).
- Whether a UI (DataFlint/History Server) is wanted for human consultants, or only
  agent-consumable metrics (then History Server + sparkMeasure, no DataFlint).
- Whether the soda "Proprietary" licence finding (E8) disqualifies Soda for bank use.

## Not verified

Docker builds (daemon down), pydeequ's failure root cause (E7), DataFlint's actual
skew heat map content, Windows-without-WSL behaviour of anything.
