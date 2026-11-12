# OpenLineage Spark listener vs the thin collector — observed on identical work

## Setup (what it took to run it, Spark 3.5.1 local, OL 1.34.0)

- jar: `io.openlineage:openlineage-spark_2.12:1.34.0` from Maven Central
  (32.4 MB) into `prototype/jars/openlineage-spark.jar`.
- the jar must be on the DRIVER CLASSPATH at JVM start: `spark.jars` alone is
  too late because the listener registers during SparkContext init
  (`ClassNotFoundException` otherwise); we passed
  `PYSPARK_SUBMIT_ARGS="--driver-class-path <jar> pyspark-shell"`.
- listener FQCN: `io.openlineage.spark.agent.OpenLineageSparkListener`
  (docs pages we could reach did not spell this out; three failed attempts are
  logged in commands.log).
- transport config that worked: `spark.openlineage.transport.type=http` +
  `spark.openlineage.transport.url=http://127.0.0.1:9500` (the JSON form
  `spark.openlineage.transport={...}` produced
  `MismatchedInputException: No content to map due to end-of-input`).
- receiver: stdlib `http.server` writing POST bodies to
  `records/ol-events.jsonl` (`ol_receiver.py`), invoked by `ol_run.py`.

## What OpenLineage captured (11 events for one aggregate-and-write job)

- ONE `runId` (UUID) shared by all events of the application; app-level
  START/COMPLETE plus per-logical-action jobs with hierarchical names:
  `wf_sales_daily_olprobe`, `...map_partitions_parallel_collection`,
  `...adaptive_spark_plan.warehouse_sales_summary_ol_probe`.
- datasets as input/output PATHS with facets: `dataSource`, `schema` (full
  field list, e.g. `id:integer, amount:double, qty:integer`),
  `lifecycleStateChange`, and `columnLineage` (output column -> contributing
  input columns).
- run facets: `processing_engine`, `spark_properties`,
  `environment-properties`, `spark_applicationDetails`, `spark_jobDetails`,
  `parent` (links sub-jobs to the app run).
- job facet: `jobType`.
- NOT captured in this configuration: `spark_logicalPlan` /
  `spark_physicalPlan` / `sql` facets (absent from all 11 events — planned
  API surface exists upstream, observed capture does not include them), any
  code-commit linkage, any scheduler/manifest identity.

Noise observed: RDD-level jobs emit `map_partitions_parallel_collection`
events that list the INPUT dataset as both input and output — consumer-side
dedup/interpretation is needed.

## What the thin collector recorded for the same class of job

- per SQL EXECUTION: normalised plan hash + compact plan excerpt, read paths
  PAIRED with the (pruned) ReadSchema, write path, duration, error;
- run-level: exit code, attempt, app id, spark version, job/task counts,
  completeness with reasons;
- joins to: git commit + definition version (scheduler/manifest side),
  catalog schema versions with column-level verdicts.

## Side by side

| dimension | OpenLineage listener | thin collector (event logs) |
|---|---|---|
| run identity | UUID runId + `parent` facet | app id + run id + attempt from runner |
| plan evidence | not in observed facets | full physical plan text + normalised hash |
| schema of what was read | `schema` facet, full field list of the relation | pruned ReadSchema, per-column verdicts vs current |
| column lineage | `columnLineage` facet (free) | derivable from plan text (not implemented) |
| code/definition version | none (job name string only) | git commit + definition hash |
| retroactive history | only after deployment | any retained event log |
| absences/ambiguity | silent (no event = no fact) | gap/partial/conflicting records |
| intrusiveness | jar + outbound HTTP per job | none (reads logs after the fact) |
| infra | needs collector endpoint (Marquez etc.) | Python stdlib + files |

## Conclusion for the decision

They are complements: OL gives live, standard-shaped lineage with full schema
facets and column lineage going forward; the collector gives retroactive,
plan-level, version-joined evidence with explicit uncertainty. The first bank
version should mine event logs first and add the listener where jobs can be
modified (see decision.md, option C).
