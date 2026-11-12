# handoff.md — task 210 (sql-spark-performance-and-cost), attempt 1, worker 2 of batch 6

## Done

- All deliverables exist in this results dir:
  - `report.md` — result summary with identity block; reading-plans worked example; measurement tables.
  - `catalogue.tsv` — 44 entries, exactly 12 tab-separated columns each (verified programmatically);
    columns as the task specified.
  - `decision.md` — retro-prep format: question, 18-row evidence table, 3 options, recommendation with
    confidence and falsifiability, owner-only decisions.
  - `examples/` — 16 Python files (15 experiment scripts including e11b + `common.py`); pure PySpark, Windows+Docker safe,
    no WSL needed; `common.py` pins PYSPARK_PYTHON so UDF workers match the driver interpreter.
  - `runs/` — 26 experiment dirs with `summary.json` (wall times, per-stage task counts, max/p50 task ms,
    shuffle bytes, input bytes/records parsed from the JSON event logs), plus plan captures:
    `runs/e01_plan_reading/out.txt`, `runs/e10_partitioning/plans.txt`, `runs/*_console.txt`,
    and `runs/defaults_probe.txt` (Spark 3.5.6 default conf values).
  - `progress.md`, `checkpoint.md`, `commands.log` (slow/failed commands with exit codes and outputs).
- Environment: `venv/` (uv, python 3.11) with pyspark 3.5.6 installed inside the results dir — nothing was
  installed on the host. Longest command run: `venv/bin/python examples/e02_skew.py` (~40 s incl. three
  Spark sessions); every experiment stayed under the 500 s foreground timeout.
- No repository was edited, no branch, no commits (task allows writes only to the results dir).
- 21 of 44 catalogue rows carry local measurements; 14 web sources fetched 2026-10-17 with verbatim quotes;
  8 rows are explicitly folklore-labelled.

## Not done

- "At least 40 antipatterns **each with** a minimal reproducible example run locally": the catalogue has 44
  rows but only 21 have local runs; the rest are source-quoted (8 folklore-labelled). Cause: single worker,
  one foreground session, and several antipatterns (dynamic allocation, spot, executor sizing, snapshot
  expiry, scheduler-level items) have no faithful local[4] repro. Each such row says how to measure it on a
  real platform instead.
- Rerun of e02 for the AQE variant needed lowered `advisoryPartitionSizeInBytes` (128KB) and
  `skewedPartitionThresholdInBytes` (256KB) — defaults do nothing at demo scale; documented, not a gap.
- Hive/RDBMS dialect behaviour not executed (only Spark SQL 3.5.6); covered by docs only.

## Proposals needing a decision

- None risky was done. One standing proposal for the engagement (already in `decision.md`): check #0 should be
  "enable event logs / history server" — if the bank's platform lacks it, that is an owner-level change.

## Ready-made texts

- None requested (no PR/issue drafts for this research task).

## Verification

- `catalogue.tsv` column check: every row has exactly 12 fields (`python3` script output: "rows with !=12
  cols: none; rows: 45" including header).
- All 15 experiment scripts exit 0 (console logs under `runs/*_console.txt`; three early failures — `F.Window` import,
  python-version mismatch in UDF worker, missing pandas — were fixed and rerun; recorded in `commands.log`
  and `progress.md`).
- Spark defaults probed live rather than trusted from possibly truncated docs (`runs/defaults_probe.txt`).
- Falsification pass on the 5 most consequential claims logged in `progress.md` at 2026-10-17T20:22.

## Unverified

- Not searched: Spark structured streaming performance; GPU/RAPIDS; Databricks-specific SQL warehouses beyond
  the two pages fetched; Azure pricing; Snowflake/BigQuery engine internals; Kubernetes executor sizing
  benchmarks; Chinese-language sources; the `spark.apache.org/docs/latest/sql-data-sources-load-save-functions.html`
  page itself (referenced from the tuning page, not fetched).
- Vendor headline numbers (8x AQE, 90%/91% spot discounts, 3x-100x pandas UDF) are top-of-range vendor
  claims, quoted as such; not reproducible locally.
- Cloud vs on-prem cost deltas for a bank platform: unknown platform by task definition.
- No prompt-injection attempts were found in fetched content.
- Also not fetched (books/literature): "High Performance Spark" (Karau/Warren), "Spark: The Definitive Guide",
  and query-optimiser cost-model literature (e.g. Graefe's survey); the committer talk coverage rests on the
  single 2020 AQE blog post. folklore-labelled rows stand in for book guidance.
