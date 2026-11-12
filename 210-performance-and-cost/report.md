Executed by: glm-5.3; effort: unknown; ZCode idle subagent
Coordinator/run: coordinator model id: account:zai-offpeak-idle-plan/GLM-5.3; task 210-sql-spark-performance-and-cost; attempt 1; worker 2 of batch 6
Start: 2026-10-17T19:50:04+02:00  End: 2026-10-17T20:18:45+02:00

# Task 210 — SQL and Spark performance and cost: plans, antipattern catalogue, savings levers

**Assumptions taken (task ambiguities, conservative reading):**
- "Run locally" = PySpark 3.5.6 on `local[4]` (12-core/19GiB WSL2 host) with event logging on; all numbers are
  synthetic-data micro-benchmarks, quoted with their exact run directories, not bank data (task forbids inventing bank data).
- Windows/Docker usability: everything is plain PySpark, runnable as `docker run -it --rm -v %cd%:/w -w /w
  bitnami/spark:3.5 spark-submit examples/<name>.py`; nothing requires WSL or Linux-only tooling (the *measurements*
  were taken on the idle host's Linux because that is where this worker runs; the scripts themselves are portable).
- The two overlapping predecessor tasks are merged into one catalogue as instructed; a row that is both an
  antipattern and a lever appears once with kind `antipattern+lever`.
- Every number below carries its evidence: `runs/<experiment>/summary.json` (event-log derived) or the fetched URL.

## Deliverables

| File | Content |
|------|---------|
| `catalogue.tsv` | 44 rows (22 antipattern, 13 lever, 9 merged `antipattern+lever`), 12 columns exactly as the task names them: id, name, kind, symptom, detection, fix, how to measure, measured effect, risk, prerequisite, source URL, example path |
| `examples/` | 16 Python files (15 experiment scripts including e11b + `common.py`) with per-run event-log parsing |
| `runs/` | 26 experiment result dirs: `summary.json` (times, shuffle bytes, task stats from event logs), plans in `*_console.txt`, `e01_plan_reading/out.txt`, `e10_partitioning/plans.txt`, and `defaults_probe.txt` |
| `decision.md` | retro-prep decision document: which 10 checks and 5 levers for the first two weeks |
| `progress.md`, `checkpoint.md`, `commands.log`, `handoff.md` | process record |

## Part 1 — How to read a Spark plan (worked example, run locally)

Full output: `runs/e01_plan_reading/out.txt` (all five `explain` modes on a 4M-row fact × 200k-row dimension join).

**The five reading levels** (all printed by the script):
1. `explain(mode="simple")` — operator tree only.
2. `mode="extended"` — adds expression ids, scan locations, `ReadSchema`, `PushedFilters`, `PartitionFilters`.
3. `mode="cost"` — adds (static) statistics per operator; the level where wrong broadcast decisions are visible *before* the run.
4. `mode="formatted"` — the compact one-operator-per-line view used for review.
5. `mode="codegen"` — generated Java; rarely useful for tuning.

**What to look for, with the lines the example produced:**

- **Exchange** = shuffle boundary. PLAN 2 (broadcast disabled) shows `Exchange hashpartitioning(customer_id, 200)`
  on *both* join sides; PLAN 1 shows only one `BroadcastExchange`. Cost rule: every Exchange is network + sort
  + potential skew; joins and aggregations create them, broadcasts remove one.
- **SortMergeJoin vs BroadcastHashJoin**: measured separately in e05 — SMJ 1.64s / 27.2MB shuffled vs broadcast
  0.67s / 7.1MB. `BuildRight`/`BuildLeft` names the side materialised into a hash relation (want: the small side).
- **Skew signals in the UI / event log**: not in the static plan at all — stage detail max-task vs median-task
  runtime. e02 with AQE off: one 4661ms task among 8 (p50 255ms) — an 18x straggler; the join stage is found by
  following the Exchange's child stage.
- **What AQE changes**: the executed plan starts at `AdaptiveSparkPlan isFinalPlan=false` and *flips at runtime*:
  e04 shows the 200-partition reduce stage collapsing to 1 task (0.99s → 0.31s); e02 shows the skewed partition
  split into 6 balanced tasks once `advisoryPartitionSizeInBytes`/`skewedPartitionThresholdInBytes` are set to
  match the (tiny) demo shuffle — the defaults (64MB/256MB, probed in `runs/defaults_probe.txt`) target
  cluster-scale data and did nothing until lowered. Docs: skew handling "by splitting (and replicating if
  needed) skewed partitions"; coalescing means "You do not need to set a proper shuffle partition number"
  (spark.apache.org/sql-performance-tuning.html, fetched 2026-10-17).
- **Windows**: `Exchange SinglePartition` under a Window operator = whole dataset through one task (e12: the
  unpartitioned-window stage ran 1 task for 1725ms; the partitioned variant spread 37.7MB over 4 tasks).
- **Scan node health**: `PartitionFilters` (directory pruning) and `PushedFilters` (row-group skipping) should be
  populated for selective queries; e10 shows both states (`runs/e10_partitioning/plans.txt`).
- **Nested-loop danger**: `BroadcastNestedLoopJoin` (e12 inequality join: ~24.75M rows out of 500k×500).

## Part 1 — Antipattern catalogue highlights (21 rows carry local measurements)

| Antipattern | Measured effect (local, Spark 3.5.6, local[4]) | Where |
|---|---|---|
| Join skew + AQE split | 5.85s → 2.2s wall; straggler 4661ms → balanced 1434ms | e02 |
| AQE coalescing | 0.99s/200 tasks → 0.31s/1 task | e04 |
| Missing broadcast | SMJ 1.64s/27.2MB → BHJ 0.67s/7.1MB | e05 |
| Python UDF | 2.82s → 0.24s as builtin (11.8x) | e06 |
| Small files (200 vs 4) | read 0.6s → 0.18s; write 5.91s → 0.43s | e07 |
| CSV vs Parquet | scan 1.16s/121MB read → 0.31s/3.8MB read | e08 |
| Codecs (none/snappy/gzip/zstd) | 36.4/17.1/6.7/5.1MB; scan 0.45/0.20/0.18/0.15s | e09 |
| Partition pruning | 1.12MB/2M rows with filter vs 16.5MB full scan | e10 |
| Column-wrapper filter vs pushdown | 27.7MB/6M rows vs 21.7MB/3.36M rows read | e10 |
| Window without partitionBy | window stage: 1 task, 1725ms, full shuffle through it | e12 |
| collect() 2M rows | 4.54s vs 1.18s parquet write | e12 |
| select * write | 2.1MB/0.62s vs 555KB/0.3s for 3 needed columns | e13 |
| repartition(200) before write | 3.34s/200 files vs coalesce(4) 0.39s/4 files | e13 |
| Bucketed join | 0.38s/0 shuffle vs 1.35s/27.9MB (plan: no Exchange) | e14 |
| Single gzip file | 5.06s vs 1.75s splittable snappy | e14 |
| Shuffle partition count | sp4 1.43s / sp16 1.13s / sp200 1.32s / sp1000 2.48s | e03 |

**Honest negatives (kept in the catalogue):**
- `cache()` was **slower** locally in both variants — cheap lineage 2.67s → 3.94s cached, window lineage
  4.66s → 5.43s (local NVMe re-read is cheap; the Databricks disk-cache doc positions platform caching
  differently). Catalogue row A12 carries this as the primary evidence.
- Spark 3.5 *folds* `cast(year as int) = 2023` into `PartitionFilters` (pruned to 2M/6M rows) — the classic
  "cast defeats pruning" folklore is only true for wrappers around data columns on this version; always verify
  in the Scan node (row A11).

## Part 2 — Cost levers (8 of 13 measured locally; sources for the rest)

Measured locally: shuffle sizing (e03), AQE (e02/e04), broadcast (e05), compaction (e07), format (e08),
codec (e09), partitioning (e10), bucketing (e14). Source-based with quotes and numbers:
- **Executor/memory sizing** — Databricks: "If you observe significant spill to disk or OOM errors, increase the
  amount of memory"; "Having fewer nodes reduces the impact of shuffles" (fetched 2026-10-17).
- **Dynamic allocation** — requires external shuffle service or shuffle tracking; K8s cannot use ESS
  (spark.apache.org/job-scheduling.html, fetched 2026-10-17).
- **Spot/preemptible** — AWS "up to a 90% discount", GCP "up to 91%" with "30 seconds to shut down"
  (aws.amazon.com/ec2/spot, cloud.google.com/spot-vms, fetched 2026-10-17).
- **FinOps / unit costs** — BigQuery on-demand "$6.25 / 1 tebibyte" (first TiB free monthly); FinOps allocation:
  "costs should be apportioned to those responsible" (cloud.google.com/bigquery/pricing,
  finops.org/framework/capabilities/allocation/, fetched 2026-10-17).
- **Table maintenance** — Delta OPTIMIZE/ZORDER, auto compaction; Iceberg rewriteDataFiles, expireSnapshots
  (docs.delta.io/optimizations-oss.html, iceberg.apache.org/docs/latest/maintenance, fetched 2026-10-17).
- **AQE headline** — "up to an 8x speedup" on TPC-DS, "32 queries had more than 1.1x speedup" (Databricks
  blog 2020-05-29 by Wenchen Fan et al., fetched 2026-10-17).

**How to measure each lever before/after** is column 7 of `catalogue.tsv`: time (wall), shuffle bytes, input
bytes/records, file counts, task distributions — all four extractable from event logs, which is why enabling
event logs is check #0 in `decision.md` (the parser is `examples/common.py::summarise_eventlog`).

## Verdict on evidence quality

- 21 of 44 catalogue rows have local measurements (script + `runs/` evidence); 14 URLs fetched 2026-10-17 with
  verbatim quotes in the TSV/decision.md; 8 rows are practice/folklore-labelled (A21, A22, A24, A39, A41, A44,
  parts of A19/A23) — each says so explicitly in its row.
- Falsification pass on the 5 most consequential claims is logged in `progress.md` (2026-10-17T20:22): two held,
  two held-with-nuance (AQE thresholds, pruning casts), one refuted as a blanket claim (cache), one weakened
  (small-files read gain partly reflects data-skipping layout, not only file-open cost — records read differed
  1.09M vs 400k between layouts).

## What could not be verified (also in handoff.md)

- No cluster-scale or cloud platform was available: dynamic allocation, spot capacity, executor sizing,
  remote-storage caching are source-quoted only. Local magnitudes will not transfer 1:1.
- No Hive/RDBMS dialect was executed; only Spark SQL 3.5.6.
- Bank-specific facts (on-prem vs cloud, versions, job inventory) are unknown by task definition and untouched.
