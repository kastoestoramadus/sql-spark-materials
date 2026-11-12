# decision.md — task 210 (retro-prep)

## 1. Question

Which 10 checks and which 5 savings levers give the most value in the first two weeks of consulting at a bank
whose SQL/Spark platform is unknown (on-prem or cloud, Spark SQL with maybe Hive/RDBMS dialects), when the
analysis must run on Windows with Docker and no WSL?

## 2. Evidence table

| # | Evidence | Source (all fetched 2026-10-17 unless "local") | Bearing |
|---|----------|------------------------------------------------|---------|
| E1 | AQE "yielded up to an 8x speedup" on TPC-DS; gains "from dynamic partition coalescing and dynamic join strategy switching" | Databricks blog by Wenchen Fan, Herman van Hövell, MaryAnn Xue, 2020-05-29, https://www.databricks.com/blog/2020/05/29/adaptive-query-execution-speeding-up-spark-sql-at-runtime.html | AQE state is check #1: one config, outsized effect |
| E2 | AQE + skew join + coalescing all default-on in Spark 3.5.6; shuffle.partitions=200; broadcast threshold 10MB; maxPartitionBytes 128MB | local probe `runs/defaults_probe.txt` (2026-10-17, Spark 3.5.6) | on a modern platform the first finding is often "someone turned AQE off" or "version < 3.2" |
| E3 | Skew straggler 4661ms vs p50 255ms (18x); AQE split → 2.2s vs 5.85s wall | local e02, `runs/e02_*/summary.json` (2026-10-17) | event-log max/p50 task ratio is a cheap, reliable skew detector |
| E4 | Broadcast vs SMJ: 0.67s/7.1MB vs 1.64s/27.2MB shuffle | local e05 (2026-10-17) | join-strategy check pays immediately, visible in one explain |
| E5 | Small files: read 0.18s (4 files) vs 0.6s (200 files); write 0.43s vs 5.91s | local e07 (2026-10-17) | compaction lever measurable with a listing + one query |
| E6 | "More data files leads to more metadata stored in manifest files"; rewriteDataFiles "combine small files into larger files to reduce metadata overhead and runtime file open cost" | Iceberg docs, https://iceberg.apache.org/docs/latest/maintenance/ (2026-10-17) | same lever on Iceberg; Delta: "Delta Lake can improve the speed of read queries ... by coalescing small files into larger ones" (https://docs.delta.io/latest/optimizations-oss.html) |
| E7 | CSV scan 1.16s/121MB vs Parquet 0.31s/27MB (input read 121MB vs 3.8MB) | local e08 (2026-10-17) | format check is a one-query measurement |
| E8 | Compression: none 36.4MB → zstd 5.1MB, scan 0.45s → 0.15s | local e09 (2026-10-17) | codec lever cheap to measure |
| E9 | Partition pruning: 1.12MB/2M rows read with filter vs 16.5MB/2.28M+ full scan | local e10 (2026-10-17) | PartitionFilters line in explain is the detector |
| E10 | Python UDF 2.82s vs builtin 0.24s (11.8x); Databricks: pandas UDFs "3x to over 100x" faster, row-UDFs "suffer from high serialization and invocation overhead" | local e06 + https://www.databricks.com/blog/2017/10/30/introducing-vectorized-udfs-for-pyspark.html (2026-10-17) | UDF audit is quick and high-yield in PySpark shops |
| E11 | collect() 2M rows 4.54s vs write 1.18s; window SinglePartition stage = 1 task; nested-loop join ~24.75M rows out | local e12 (2026-10-17) | plan smells detectable by grep on explain output |
| E12 | Bucketed join 0.38s/0 shuffle vs 1.35s/27.9MB; docs: with SPJ "the query plan will not contain Exchange nodes prior to the join" | local e14 + https://spark.apache.org/docs/latest/sql-performance-tuning.html (2026-10-17) | bucketing only pays on *repeated* joins — needs job history |
| E13 | Cache measured LOCALLY SLOWER (2.67→3.94s; 4.66→5.43s with window lineage) on local NVMe disk | local e11/e11b (2026-10-17) | warns against cargo-cult caching; Databricks recommends *automatic disk caching* instead (https://docs.databricks.com/en/optimizations/disk-cache.html) |
| E14 | Spot: "up to a 90% discount" (AWS), "up to 91%" (GCP, "30 seconds to shut down") | https://aws.amazon.com/ec2/spot/ and https://cloud.google.com/spot-vms (2026-10-17) | biggest cloud cost lever, but needs restartable jobs (owner decision) |
| E15 | Unit cost anchor: BigQuery on-demand "$6.25 / 1 tebibyte", "The first 1 TiB of query data processed per month is free"; FinOps: "Allocation defines how costs should be apportioned to those responsible" | https://cloud.google.com/bigquery/pricing and https://www.finops.org/framework/capabilities/allocation/ (2026-10-17) | without tags/unit costs no lever can be prioritised by money |
| E16 | Dynamic allocation needs external shuffle service or shuffleTracking; K8s "doesn't yet support the external shuffle service" | https://spark.apache.org/docs/latest/job-scheduling.html (2026-10-17) | lever available only after infrastructure prerequisite |
| E17 | Executor sizing: "If you observe significant spill to disk or OOM errors, increase the amount of memory"; "Having fewer nodes reduces the impact of shuffles" | https://docs.databricks.com/en/compute/cluster-config-best-practices.html (2026-10-17) | sizing lever is source-guided, not locally measurable |
| E18 | Event log: "useful for reconstructing the Web UI after the application has finished" | https://spark.apache.org/docs/latest/configuration.html (2026-10-17) | every check below depends on event logs existing — check #0 |

## 3. Options

**Option A — "Plan-first ten": read plans and event logs for the top-20 jobs, fix what the plans name.**
- Cost: 2 engineers x 2 weeks; needs only explain() + event logs + `evlog.py`-style parser (all Windows/Docker-safe).
- Benefit: every finding is causally evidenced (a plan node), no platform change needed; catches skew, missing
  broadcast, nested loops, single-partition windows, UDFs, pushdown defeats in one pass (E3, E4, E10, E11).
- Risk: finds query-level waste but not fleet-level waste (sizing, spot, duplication) — the biggest money items (E14, E15).

**Option B — "Config-first": audit platform configs and table layouts (AQE, shuffle partitions, file sizes,
formats/partitioning, compaction) before touching queries.**
- Cost: 1 week, mostly metadata/listing work.
- Benefit: one-line config fixes (AQE on, thresholds) propagate to ALL queries (E1, E2); compaction/format
  levers have the largest measured multipliers (E5–E9).
- Risk: wrong without per-job evidence: AQE/coalescing interacts with skew thresholds (measured E3: defaults
  did nothing on small shuffles); compaction costs rewrites; needs the job list to rank tables.

**Option C — "Cost-first": build the unit-cost map (tags, cost per job/TB) then attack the top spenders.**
- Cost: depends entirely on billing/tag access the bank may not have granted in week 1.
- Benefit: the only option that can prove savings in currency, which is what the engagement sells.
- Risk: blocked on owner-side access (E15); zero query improvements while the map is built.

## 4. Recommendation

Hybrid, sequenced A→B with C started in parallel (owner-dependent):

**The 10 checks of weeks 1–2** (each is a grep-able plan signal or an event-log number; all reproduce with the
scripts in `examples/`):
1. Event log / history server exists (E18) — else enable; every later check depends on it.
2. Spark version + AQE state and sub-flags, shuffle partition default, broadcast threshold (E1, E2).
3. Per-stage straggler scan: max vs p50 task runtime in event logs → skew (E3).
4. Join strategy audit in top jobs' plans: SMJ where a side is small; BroadcastNestedLoopJoin at all (E4, E11).
5. Exchange SinglePartition (window without partitionBy / global sort) in plans (E11).
6. Python UDF inventory (BatchEvalPython nodes; column-level usage) (E10).
7. Pushdown audit: PushedFilters/PartitionFilters empty on Parquet/Delta/Iceberg scans (E9).
8. File health: files-per-table listing, median file size, empty partitions (E5, E6).
9. collect()/toPandas()/count-for-existence patterns in repo grep (E11 + catalogue A08/A22).
10. Recomputation audit: same scan stages repeated across jobs in one notebook/DAG run (E13 — and verify, do
    not assume cache helps: measured slower locally).

**The 5 savings levers** (ranked by measured/quoted effect over effort, assuming checks confirm them):
1. AQE on with thresholds sanity-checked per real shuffle sizes — up to 8x quoted, config-only (E1).
2. Compaction / OPTIMIZE / rewriteDataFiles on the hottest wide tables — 3.3x read locally, plus write-side
   13.7x; supported natively by Delta/Iceberg (E5, E6).
3. Columnar format + codec on remaining CSV/JSON/uncompressed tables — 3.7x scan, 7x size reduction (E7, E8).
4. Broadcast/join-strategy fixes on the top recurring joins — 2.4x, plan-guided (E4).
5. Partition design + pruning repair on big scanned tables — 1/3 of bytes in the local 3-partition demo,
   scales with partition count (E9).
   (Spot capacity (E14) is the biggest *money* lever in cloud but is an owner decision, not a week-2 lever.)

**Confidence: medium-high (4/5) for the check list** — it rests on 21 local measurements across 14 experiment
scripts plus 14 fetched sources; the local effects are real but measured on local[4] with NVMe, so magnitudes
will differ at the bank. **Medium (3/5) for the lever ranking** — magnitudes are from synthetic data and
vendor pages (Databricks/AWS/GCP have incentive to quote the top of the range), and lever #2/#3 assume the
bank's tables are actually in the named bad state, which only the checks can confirm.

**What would change my mind:** (a) finding the platform is < Spark 3.2 or Hive-only (AQE lever dies, bucketing
and CBO rise); (b) billing/tag access granted early (Option C jumps first — money beats multipliers); (c) a
table-format-less shop (Parquet-on-HDFS) where Delta/Iceberg levers become rewrite projects, not levers.

**How many cases the rule rests on:** the plan-smell checks rest on 21 local synthetic cases + the patterns
documented in 4 vendor/doc sources; no real bank workload was available (task forbids inventing bank data).
The skew/AQE/broadcast/compaction rows are corroborated by two independent source kinds (local run + docs);
11 of 44 catalogue rows are single-source (labelled in `catalogue.tsv`), and 8 are folklore-labelled practice
with no measurement.

## 5. What only the owner can decide

- Whether billing/tag data may be read and which unit cost (per TB scanned, per job run, per pipeline) the
  bank reports savings in (E15).
- Whether jobs may move to spot/preemptible capacity (restartability, SLAs) (E14).
- Whether table formats may change (CSV→Parquet, or adopting Delta/Iceberg tooling) — a data-platform
  governance decision, not a tuning one.
- Access to the job history / scheduler (Airflow etc.) for the duplicate-pipeline and dependency-pruning
  levers (A33/A34), which need an inventory no agent can build alone.

## What I could not verify

- On-prem vs cloud behaviour differences for the bank (unknown platform by task definition).
- The 8x/90%/91% headline numbers (vendor pages, top-of-range; not reproducible locally).
- Whether the bank's Spark is 3.2+ (AQE default) or older — first thing to check on site.
- Dynamic allocation benefits without a shared cluster to observe (E16).
- No real SQL dialect other than Spark SQL 3.5.6 was executed locally (Hive/RDBMS dialects are covered by
  sources only).
