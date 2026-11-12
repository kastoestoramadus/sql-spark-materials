Executed by: GLM-5.3 (account:zai-offpeak-idle-plan/GLM-5.3); effort: unknown; ZCode idle subagent
Coordinator/run: coordinator model id: account:zai-offpeak-idle-plan/GLM-5.3; task 190-sql-spark-evidence-collector; attempt 1; worker 7 of batch 2
Start: 2026-10-18T19:49:29+02:00  End: 2026-10-18T20:12:05+02:00

# Evidence collector for Spark/SQL platforms: survey, provenance model, working prototype

Everything below was RUN in this sandbox unless marked "source claim". The
prototype is reproducible with `prototype/run_all.sh` (needs `system/env.sh`
for java). Synthetic data only; no credentials; results dir only.

## Step -> evidence map (prompt-audit requirement)

| Do step | status | evidence |
|---|---|---|
| 1 survey >=25 sources | ok (27 rows; 2 weak) | `survey.tsv`; licences/stars/activity from GitHub API 2026-10-18; per-row primary URL + quotes |
| 2 provenance model | ok | `provenance-model.md` (envelope, per-kind version pins, JSON example of every record kind incl. gap), matched 1:1 by `prototype/collector.py` |
| 3 prototype + 3 queries + OpenLineage | ok (ran end to end) | `prototype/` — 3 workflows + shadow app, 2 rounds with code change (commits cdd939f/3c40d07) and a customers DDL v1->v2 between rounds, failed purge run, crashed attempt with orphan event log, paged manifest listing; final collect: 39 records over 9 apps/8 runs; `prototype/outputs/query-{a,b,c}.txt`, `query-c-sales-summary.txt`; OL listener jar 1.34.0 captured 11 events -> `openlineage-comparison.md` |
| 4 agent-facing side | ok | `agent-interface.md` (CLI, SQL views v_latest_attempted/successful + v_run_plan_hashes, deterministic analyses) |
| 5 risks/bank constraints | ok | `risks.md` |
| decision | ok | `decision.md`: thin collector first, OL listener as complement, catalogue deferred |
| task-specific checks | ok (one unexercised) | pagination (2 pages), omitted workflow (gap: shadow app), failed run (purge exit 1), retry/attempt (a1 kill, a2 success), changed definitions (v1/v2), schema change after run (customers DDL), latest-attempted vs latest-successful defined in code+docs and DEMONSTRATED (query-a: purge latest attempted failed, latest successful differs), completeness field on every record, ambiguous-join rejection implemented (app-id conflict -> `conflicting`) but not exercised by data — stated as such |

## Observed results (quoted from the run)

- `collector: 39 records ({'workflow-definition': 6, 'run': 8, 'metrics': 7, 'plan': 10, 'gap': 2, 'table-schema': 6}), manifests=3 in 2 pages, apps=9, runs=8`
- query-a excerpt: `wf_gdpr_purge: latest attempted wf_gdpr_purge--r1--a2 exit=1 ... latest SUCCESSFUL differs: wf_gdpr_purge--r2--a1 ... (latest attempted failed)`
- query-c excerpt (customers): `wf_risk_report--r1--a2: POSSIBLY OLDER - pruned subset and run predates current version`, `wf_risk_report--r1--a1: UNKNOWN (no scan evidence for customers)`, `wf_risk_report--r2--a1: current`
- mypy --strict on all six collector-side Python files: `Success: no issues found in 6 source files`

## Key findings (each with its check)

1. Spark event logs already carry the core evidence: per-execution physical
   plan, pruned ReadSchema, job/task metrics (parsed here; History Server REST
   serves the same, survey row `spark-hs`). The collector therefore needs no
   new instrumentation for retroactive analysis.
2. The event-log ReadSchema is column-PRUNED (count-only scans carry
   `struct<>`) — so "which schema version did this run read" can be proven
   only for touched columns; the model emits verdicts (NOT CURRENT /
   POSSIBLY OLDER / UNKNOWN / current) instead of guessing. Catalogs are
   current-only (Hive metastore row; Postgres/MySQL information_schema rows).
3. Absences are facts: the crashed attempt left an orphan event log and no
   appinfo -> run `partial` + `gap` record; the shadow app (not in manifests)
   -> second `gap`. Cross-checked against raw SparkListenerApplicationStart
   entries.
4. OpenLineage (1.34.0, Spark 3.5.1 local): captures runId + hierarchical jobs
   + dataset paths + full schema facets + columnLineage + parent; did NOT emit
   plan/sql facets in this configuration; needs driver-class-path at JVM start
   and works only going forward — complement, not substitute (details and the
   three failed configurations in `openlineage-comparison.md` / commands.log).
5. Ecosystem: Amundsen archived (two sources); Marquez/DataHub/OpenMetadata
   active; Control-M API docs 403 to us; Unity Catalog OSS APIs "currently
   evolving" (survey.tsv).

## Shortfalls and limits (no padding)

- Survey rows with weak in-page evidence: `control-m` (HTTP 403), `glue`
  (AWS pages rendered title-only; GetTableVersions claim is model knowledge,
  unverified), `airflow` field list (endpoint paths quoted; DAGRun schema
  fields not visible in truncated page), `atlas` (title only).
- The `conflicting` (app-id mismatch) join path is implemented but no data
  pair exercised it.
- No column-removal scenario in the synthetic data, so the definite
  "not-current" verdict was unit-checked (fires for absent column / type
  change) rather than observed end to end.
- Plan-hash normalisation ignores AQE final-plan variability; two runs of one
  code version were not compared at scale.
- OL schema-facet completeness (vs pruning) left as an open question (single
  observation, job reads all columns).
- Not searched/attempted: paid/vendor doc mirrors, actual Control-M or Glue
  API calls (no credentials by design), Dagster/Atlas field-level API pages
  (landing pages were shells), Spark 4.x behaviour.

All decisions taken: toy platform shape (file manifests + SQLite catalog +
parquet warehouse) chosen per the task's allowance; "latest attempted"
defined as max start over all attempts regardless of outcome; catalog never
used as historical truth; no host files touched outside the results dir.
