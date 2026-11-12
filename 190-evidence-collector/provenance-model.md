# Provenance model: the tagged evidence record

Design tested by `prototype/` (records in `prototype/records/records.jsonl`,
queryable copy in `prototype/records/evidence.db`). Every example below is
abbreviated from a real record produced by the run on 2026-10-18.

## 1. The envelope

One record per collected fact, JSON, one line, append-only:

```
record_id      content address: sha256(canonical JSON without record_id)[:16];
               collecting the same fact again yields the SAME id (idempotent)
kind           workflow-definition | run | plan | metrics | table-schema | gap
subject        {id, type}: stable id of the thing the record is about
version        how THIS piece pins the version of what it describes (per kind, below)
source         {system, endpoint, collected_at, collector_version}: where and when
payload        the fact itself (raw-ish: plan excerpt, metrics, manifest, schema)
completeness   {status, reasons}: complete | partial | unknown |
               current_snapshot_only | conflicting
links          ids of records this one refers to (plan -> run -> definition ->
               commit; plan -> table-schema evidence it ran against)
```

`completeness` is the load-bearing addition over plain ETL: a record states how
trustworthy its own version pin is. Joins that would silently guess are instead
rejected or downgraded (`conflicting`, `partial`) and surface in queries.

## 2. Version definition per kind

| kind | subject id | version pin | notes |
|---|---|---|---|
| workflow-definition | workflow id | git commit + definition_version + sha256 over manifest+entry+shared harness at that commit | content obtained with `git show <commit>:path`, so history survives later edits |
| run | run id (workflow + round + attempt baked in) | attempt number + app_id + code_commit + definition_version/hash | app_id comes from the runner's appinfo file; if absent, completeness=partial |
| plan | run id + `#exec<executionId>` | same as its run + plan_hash | plan_hash = sha256 of the NORMALISED physical plan (below) |
| metrics | run id | app_id + attempt | counts and durations from the event log |
| table-schema | table name | version + schema_hash of the CURRENT catalog row | always `current_snapshot_only`; NEVER used as the schema a past run read |
| gap | app id | app_id | unmapped applications, missing runs: the model stores absences as facts instead of dropping them |

Plan normalisation (implemented in `collector.py:normalise_plan`): absolute
warehouse prefix -> `<WH>`, expression ids `#123` -> `#`, all whitespace
collapsed. It deliberately ignores node numbering and machine-local paths, so
the same logical plan on another machine hashes equal; it also ignores plan
STAGE boundary counters, which can differ between AQE replanning — a known
limitation: two runs of the same code can hash differently if AQE final plans
diverge (observed risk, not observed in the toy data).

## 3. Detecting "different versions of the same thing"

- Two records about the same subject id with different version pins = different
  versions (e.g. `wf_sales_daily` at commit `cdd939f` vs `3c40d07`).
- Same pin, different content hash = collection inconsistency -> investigate.
- Different pin, same plan_hash after normalisation = a CODE change that did not
  change the executed plan (strong signal for "definition edit was cosmetic").
- The catalog cannot answer "which schema version did run R read": Spark's
  event-log `ReadSchema` is column-PRUNED (observed: count-only scans carry
  `struct<>`). So the collector compares read columns against the current
  schema per column and emits verdicts, not guesses:
  `matches-current-columns`, `subset-of-current (pruned read)`,
  `not-current (column X absent/type differs)`, `no-columns-read`.
  Only the third proves a different schema version. The query layer combines
  this with run start vs catalog `updated_at` to say "POSSIBLY OLDER" instead
  of silently joining.

## 4. Storage: append-only, diffable

- `records.jsonl`: one canonical-JSON line per record; re-collection appends
  only lines whose record_id is not present (content addressing makes this a
  no-op for unchanged facts). `diff` of two sorted snapshots = what changed
  between collections.
- `evidence.db` (SQLite): the same records in a `records` table plus ready-made
  views (`v_latest_attempted`, `v_latest_successful`, `v_run_plan_hashes`) for
  SQL-speaking consumers. DuckDB would serve the same role for larger volumes;
  large raw plans can move to content-addressed files with the hash in payload
  (not needed at prototype scale).

## 5. Real examples (abbreviated, from the run)

workflow-definition:
```json
{"record_id": "5c1a7e5091ff2931", "kind": "workflow-definition",
 "subject": {"id": "wf_sales_daily", "type": "workflow-definition"},
 "version": {"code_commit": "cdd939f1254b6076182c260ebec87fa820ab4aa3", "definition_version": 1},
 "source": {"system": "toy-platform", "endpoint": "git cdd939f... manifests/wf_sales_daily.json",
            "collected_at": "2026-10-18T18:05:04+00:00", "collector_version": "collector 0.1"},
 "payload": {"manifest": {"reads": ["raw_sales"], "writes": ["sales_summary"], "...": "..."},
             "definition_hash": "41bf43e93b80b4a4"},
 "completeness": {"status": "complete", "reasons": []},
 "links": {"code_commit": "cdd939f1254b6076182c260ebec87fa820ab4aa3"}}
```

run (the crashed attempt — note completeness):
```json
{"record_id": "...", "kind": "run",
 "subject": {"id": "wf_risk_report--r1--a1", "type": "run"},
 "version": {"attempt": 1, "code_commit": "cdd939f...", "definition_version": 1},
 "payload": {"app_id": null, "exit_code": -9, "crash_simulated": true, "...": "..."},
 "completeness": {"status": "partial", "reasons": ["no appinfo (killed before start?)"]},
 "links": {"plans": []}}
```

plan:
```json
{"record_id": "...", "kind": "plan",
 "subject": {"id": "wf_risk_report--r1--a2#exec0", "type": "plan"},
 "version": {"run_id": "wf_risk_report--r1--a2", "execution_id": 0, "code_commit": "cdd939f..."},
 "payload": {"plan_hash": "e7a81d149d73e8a6", "read_tables": [
    {"table": "customers", "read_columns": [["id","int"],["name","string"]],
     "catalog_match": "subset-of-current (pruned read)", "...": "..."}],
   "write_paths": ["<...>/warehouse/risk_flags"], "...": "..."},
 "links": {"run": "wf_risk_report--r1--a2", "code_commit": "cdd939f...",
           "table_schemas": ["customers", "sales_summary"]}}
```

metrics:
```json
{"kind": "metrics", "subject": {"id": "wf_gdpr_purge--r1--a1"},
 "version": {"app_id": "local-1792346504422", "attempt": 1},
 "payload": {"num_sql_executions": 1, "num_jobs": 2, "failed_jobs": 0,
             "num_tasks": 2, "duration_ms": 3211}}
```

table-schema (current snapshot, honestly labelled):
```json
{"kind": "table-schema", "subject": {"id": "customers"},
 "version": {"version": 2, "schema_hash": "728620c248b3fb4a"},
 "payload": {"dtypes": [["id","int"],["name","string"],["segment","string"]],
             "updated_at": "2026-10-18T18:02:05+00:00"},
 "completeness": {"status": "current_snapshot_only",
   "reasons": ["catalog holds the latest version only; schemas read by past runs come from event logs or are unknown"]}}
```

gap (the shadow app and the crashed attempt's orphan event log):
```json
{"kind": "gap", "subject": {"id": "local-1792346494449"},
 "payload": {"gap_type": "unmapped_application",
             "app_name": "wf_shadow--r1--a1",
             "note": "app present in event logs, absent from manifests/run index"},
 "completeness": {"status": "partial", "reasons": ["no workflow mapping"]}}
```

## 6. Comparison with OpenLineage

OpenLineage (spec quoted in `survey.tsv`, row `openlineage-spec`) already
defines: a RunEvent with a UUID `runId` per run, job identity
namespace+name ("The Job evolves over time, and this change is captured when
the job runs"), dataset facets including `schema`, `columnLineage`, `version`,
and job facets `sourceCodeLocation`, `sql`.

What this model ADDS over plain OpenLineage consumption:
1. version pins OUTSIDE the job: git commit of the workflow repo joined to the
   run via the scheduler's run record (OL has `sourceCodeLocation` but no
   guarantee it matches what actually executed);
2. pruning-aware schema provenance: which table schema version a run READ,
   with explicit uncertainty instead of a facet snapshot only;
3. normalised plan hashes for deterministic plan-regression diffing;
4. completeness + gap records: absences (unmapped apps, missing artifacts,
   ambiguous app-id joins) are stored facts;
5. append-only raw evidence store (OL consumers typically keep only the latest
   graph state in a catalogue).

What it REUSES from OpenLineage: the Spark listener as a collector (see
`openlineage-comparison.md`), facet vocabulary (schema, columnLineage,
sourceCodeLocation, parent) and the runId as the canonical cross-system run
correlator. Marquez/DataHub can sit downstream of the same events.
