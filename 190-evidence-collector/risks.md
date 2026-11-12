# Risks and bank constraints

Environment assumption from the task: Windows with Docker (no WSL); models
Opus/Sonnet/a GPT model; a Spark/SQL platform at a bank.

## Access rights (what must be asked of the bank)

1. History Server: read access to the UI/REST port and/or a copy of
   `spark.eventLog.dir` (read-only share or periodic sync). Event logs are the
   only complete run-time truth (plans, metrics, ReadSchema); without them the
   collector degrades to current-snapshot joins.
2. Metastore/catalog: a READ-ONLY service account (Hive metastore thrift 9083,
   `information_schema` SELECT, or Glue `GetTable*` with read-only IAM).
3. Scheduler APIs: Airflow REST token (read scope), Oozie/Control-M read
   endpoints, Control-M is behind docs that returned HTTP 403 to us — expect
   an internal mirror or a vendor contact.
4. Git: clone/commit-hash read access to workflow repos (or the scheduler's
   `dagSources`-style endpoint); the whole code-version pin rests on this.
5. Network routes from the collector host (Windows/Docker) to those endpoints;
   likely a firewall change request per route.

## Data privacy

- Physical plans and SQL text can contain LITERALS (filter values, IN-lists)
  and business column names. The collector must run a redaction step before
  storing: mask string/number literals in `physicalPlanDescription` and SQL,
  keep column names only if the bank approves (they are usually needed for
  reasoning — decide explicitly).
- Event logs additionally contain user names, host names, IPs
  (SparkListenerApplicationStart.User, executor host/port) — strip or hash.
- Collected evidence store inherits bank data classification; retention and
  who may open `evidence.db` need a policy line before the first collection.

## Load on production systems

- Read-only and cheap by design: one pass over event logs (file reads),
  metastore batch reads, scheduler REST with pagination (`limit/offset`,
   Oozie `offset/len`).
- Polling limits: collect incrementally by mtime/run id watermark, not full
   scans; back off on 429/5xx; agree a polling interval with platform owners.
- History Server itself is usually already serving the UI; adding one REST
  reader is negligible, but large event-log replays on HS cost CPU — prefer
  reading the log directory directly when allowed.
- Spark-side listeners (OpenLineage/Spline) add small per-job overhead and an
  outbound HTTP dependency; in restrictive zones prefer the offline event-log
  collector (this prototype's default mode).

## Windows/Docker constraints

- Everything in the prototype is plain Python + SQLite + a JVM for Spark:
  runs inside Docker Desktop Linux containers on Windows; the collector
  itself (stdlib only) runs native on Windows too.
- No WSL assumed: avoid pipelines that shell out to unix tools; the collector
  uses only `git` + Python stdlib (+ PySpark in the toy platform).
- Spark Connect is the natural way for an agent on Windows to inspect a live
  Spark platform without a local JVM (thin client, quoted in survey.tsv).

## Failure modes observed in the prototype (design answers)

- App killed before writing identity -> run record `partial`, no plan records;
  queries report UNKNOWN rather than borrowing another run's plan.
- Event log exists but no run/index entry -> `gap` record (unmapped app).
- App-id mismatch between sources -> join REJECTED (`conflicting`).
- Schema changed outside workflows -> catalog is current-truth only; past-run
  schemas come from event logs or stay unknown.
