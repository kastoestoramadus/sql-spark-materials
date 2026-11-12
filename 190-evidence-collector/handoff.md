# Handoff — task 190

## Done

- Survey: `survey.tsv` (27 rows; licence/stars/push-date via GitHub API
  2026-10-18; per-row primary URLs and quotes; weak rows flagged).
- Design: `provenance-model.md` (tagged evidence record envelope, version pins
  per kind, append-only JSONL + SQLite storage, OpenLineage comparison),
  `agent-interface.md`, `risks.md`, `decision.md` (recommendation: thin
  collector first, OL listener as complement, catalogue deferred).
- Working prototype in `prototype/` (reproducible: `. system/env.sh` then
  `prototype/run_all.sh`):
  - toy platform: `repo/` git history `main` with tags `round1` (cdd939f) and
    `round2` (3c40d07); workflows wf_sales_daily / wf_risk_report /
    wf_gdpr_purge + unlisted wf_shadow; SQLite catalog `wh.py`; parquet
    warehouse; schema DDL between rounds (customers v1 -> v2).
  - runner (`runner.py`) writes `runs/index.jsonl` with commit, definition
    hash, attempt, exit code, appinfo; crash simulation kills attempt 1.
  - collector (`collector.py`) -> `records/records.jsonl` +
    `records/evidence.db` (views v_latest_attempted, v_latest_successful,
    v_run_plan_hashes); queries a/b/c -> `outputs/query-a.txt`,
    `query-b.txt`, `query-c.txt` (customers), `query-c-sales-summary.txt`.
  - OpenLineage probe: jar `jars/openlineage-spark.jar` (1.34.0),
    `ol_run.py` + `ol_receiver.py`, captured `records/ol-events.jsonl`
    (11 events); comparison in `openlineage-comparison.md`.
  - mypy --strict clean on wh/runner/collector/seed/change_schema/ol_receiver.
- Report with step->evidence map: `report.md`; run log `progress.md`,
  `commands.log`, `checkpoint.md`.

## Not done

- Control-M Automation API survey row: docs.bmc.com returned HTTP 403; no
  alternative source reached (marketing pages add nothing).
- AWS Glue row is weak: both docs URLs rendered title-only; GetTableVersions
  VersionId claim unverified this run (needs a re-fetch or aws cli with a
  throwaway account).
- Airflow DAGRun field-level schema: spec file too large for the fetcher's
  truncation; endpoint paths ARE quoted. Alternative: download
  airflow/api_connexion/openapi/v1.yaml and grep locally.
- Atlas/Dagster field-level rows: landing pages empty shells; repo stats used.
- Spark History Server itself was not started locally (its data source, the
  event logs, was parsed directly instead; REST equivalence rests on the
  monitoring docs quote).
- No real scheduler (Airflow/Oozie) was run; scheduler rows are doc-based.

## Proposals needing a decision

- None requiring risky action. Possible follow-up work (owner's call, do not
  start without approval): an Airflow adapter for the collector reading
  /dags/{dag_id}/dagRuns + dagSources; a redaction filter for
  physicalPlanDescription literals before storage at a real site.

## Ready-made texts

- None (no PRs/issues were in scope; nothing was pushed or posted).

## Verification

- `prototype/run_all.sh` ran end to end (three debug passes, final clean pass):
  final collect line quoted in report.md; queries produced the three required
  answers incl. the latest-attempted-failed divergence and POSSIBLY-OLDER
  schema verdicts.
- Gap records cross-checked against raw event-log SparkListenerApplicationStart
  entries (9 apps, 2 unmapped).
- Amundsen "archived" verified twice (README + GitHub API .archived=true).
- mypy --strict: `Success: no issues found in 6 source files`.
- `git -C prototype/repo status --short` clean; HEAD detached at tag round2.

## Unverified

- Glue GetTableVersions details; Control-M API surface; Airflow DAGRun field
  list; OL schema facet completeness under column pruning (single observation);
  AWS/Control-M pages also served no content; the amundsen.io redirect to
  7yardsfilm.com was NOT followed (unrelated domain, possible squatted site —
  note for the owner's browsing safety).
- No prompt-injection attempts were found in fetched content.
