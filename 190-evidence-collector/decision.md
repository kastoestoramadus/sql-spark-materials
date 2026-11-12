# Decision: what to build first for the bank engagement

## 1. Question

For the first version of the Spark/SQL evidence system at the bank: build on
OpenLineage, build the thin collector of the prototype (task part 3), or adopt
a catalogue (DataHub/OpenMetadata)?

## 2. Evidence table

| # | finding | source |
|---|---|---|
| E1 | Spark event logs already contain per-execution physical plans + pruned ReadSchema + job/task metrics; History Server REST `/api/v1/applications/[app-id]/sql` with `planDescription` serves them | spark monitoring docs (survey.tsv `spark-hs`), verified locally: `runs/eventlog/*` parsed by `prototype/collector.py` |
| E2 | Catalogues/metastores hold CURRENT schemas only: Hive metastore "records the schema version" refers to metastore-own compatibility, not table history; information_schema views are current-state (Postgres/MySQL rows) | survey.tsv `hive-metastore`, `pg-info-schema`, `mysql-info-schema` |
| E3 | ReadSchema in plans is column-PRUNED: count-only scans show `struct<>`; schema provenance needs subset semantics + explicit uncertainty | observed: `prototype/outputs/query-c.txt` verdicts |
| E4 | OpenLineage spec has runId/job/dataset + facets (schema, columnLineage, sourceCodeLocation, sql) but "The Job evolves over time" without a job-version field; no completeness/absence model | survey.tsv `openlineage-spec` |
| E5 | OpenLineage Spark listener works on Spark 3.5 local with the agent jar on the driver classpath; captures run events incl. SQL facets (see comparison for exact fields) | `prototype/records/ol-events.jsonl`, `openlineage-comparison.md` |
| E6 | Catalogues are strong at discovery, weak as evidence stores: DataHub GraphQL/REST + 150+ integrations; OpenMetadata docker/K8s; Marquez stores OL events; none pins "which code commit + which schema version did THIS run use" as first-class | survey.tsv `datahub`, `openmetadata`, `marquez` |
| E7 | Amundsen "was archived in September 2026" | survey.tsv `amundsen` (README) |
| E8 | Scheduler APIs expose runs (Airflow dagRuns + dagSources; Oozie show=definition CURRENT only; Prefect flow_runs filter) — enough to enumerate and version workflows, but definitions are current-only in several | survey.tsv `airflow-rest`, `oozie`, `prefect` |
| E9 | The thin collector (stdlib + SQLite) produced 35 records over 8 apps/7 runs with deterministic joins and honest uncertainty, incl. failed attempt, orphan event log, unmapped app, schema drift | `prototype/records/`, `prototype/outputs/` |
| E10 | Control-M Automation API docs returned 403 to us; bank-internal access will differ | commands.log / survey.tsv `control-m` |

## 3. Options

**A. Adopt a catalogue first (DataHub or OpenMetadata).**
Cost: docker stack (DataHub "Requires Docker (8GB RAM)"), ingestion setup,
connectors per source. Benefit: discovery UI, lineage, governance, agents/MCP.
Risk: evidence provenance (run↔commit↔schema-version) is not first-class;
metastore history is current-only (E2), so the core question stays unanswered;
heavy first ask of the bank.

**B. OpenLineage listener + Marquez only.**
Cost: deploy the agent jar to jobs + a Marquez instance. Benefit: standard
events, column lineage, live collection. Risk: only covers runs AFTER
deployment (no retroactive event-log mining), no scheduler/git join, no
absence/completeness records (E4); Marquez is a lineage store, not an
append-only evidence archive.

**C. Thin collector (prototype) first, OL listener where deployable.**
Cost: small Python surface, read-only access asks (event log dir, metastore,
scheduler API, git) — exactly the list in risks.md. Benefit: retroactive
(E1), deterministic joins with honest uncertainty (E3, E9), works on the
bank's Windows/Docker constraint, cheap to hand to an AI reviewer
(agent-interface.md). Risk: it is bespoke (no UI/governance); must be kept
thin or it grows into a poor catalogue; Control-M/other schedulers need
per-site adapters (E10).

## 4. Recommendation

**Option C for the first version**, with the OpenLineage listener added on the
workflows the bank can modify (it enriches plan/schema facets going forward,
E5), and a catalogue (option A) deferred until discovery/governance is asked
for — the collector's JSONL can feed one later.

Confidence: medium-high on the mechanics (prototype-verified), low on bank
politics (access, Control-M, redaction rules unverifiable from here).

What would change my mind: (i) the bank already runs DataHub/OpenMetadata
centrally — then integrate rather than duplicate; (ii) event-log retention too
short to be useful — then OL-first (B) becomes the primary source; (iii) a
mandated governance catalogue purchase.

How many cases the rule rests on: one synthetic platform shape (3 workflows,
7 runs, 8 apps, 5 tables, 2 code versions) plus 27 surveyed sources; no
production-scale run, no real scheduler tested.

## 5. Only the owner can decide

- The access requests to the bank (read-only service accounts, event-log share,
  scheduler tokens, git clone rights) and their sequencing.
- Whether a catalogue is strategically mandated (then C becomes a feed, not a
  rival).
- The redaction/retention policy for collected plans and column names.
- Effort budget for adapters beyond Spark+Airflow-shaped platforms.

## Errata 2026-10-31 (2026-10-18 code review, approved by the owner)

The text above is preserved. Where it conflicts, this section wins.

- E5: the report says no plan or SQL facets were captured. E9: verified output is 39 records / 9 apps / 8 runs, not 35 / 8 / 7.
- Seven run IDs in the original records are invalid; do not use them as content-addressed truth. Storage is a replaceable snapshot, not an audit archive.
