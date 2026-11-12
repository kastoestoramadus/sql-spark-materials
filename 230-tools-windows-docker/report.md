Executed by: GLM-5.3 (account:zai-offpeak-idle-plan/GLM-5.3); effort: unknown; ZCode idle subagent
Coordinator/run: account:zai-offpeak-idle-plan/GLM-5.3; task 230-sql-spark-tools-on-windows-docker; attempt 1; worker 8 of batch 2
Start: 2026-10-18T19:49:14+02:00  End: 2026-10-18T20:10:10+02:00

# Task 230: SQL/Spark analysis tools that run on Windows with Docker (no WSL)

Assumption taken (no owner available): "tried locally" means this WSL2 workstation,
which proves the pip/JVM/Maven tool paths work on Linux and yields runnable artefacts;
it does NOT prove Windows-without-WSL behaviour. Every such claim below is marked
documented-feasibility vs exercised-compatibility, as the audit note requires.
No bank data was used; all data here is synthetic.

## Step 0 - environment preflight (all commands in logs/, outputs quoted there)

| Check | Command | Result (2026-10-18) |
|---|---|---|
| spark.apache.org / github.com / arxiv.org / pypi.org | `curl -sS -o /dev/null -w "%{http_code}"` | 200 / 200 / 200 / 200, all < 0.5 s |
| java | `java -version` | OpenJDK 17.0.15 Corretto |
| python3 | `python3 --version` | 3.13.16 (host); venvs use CPython 3.11.17 via uv |
| uv | `uv --version` | 0.13.1 |
| docker | `docker --version` | WSL shim fails; `docker.exe` = Docker 24.0.7 |
| docker run | `timeout 60 docker.exe run --rm hello-world` | FAILED: "open //./pipe/docker_engine: The system cannot find the file specified" (Docker Desktop daemon down) => all Dockerfiles untested |

venvs (UV_CACHE_DIR and .ivy2 inside the results dir; nothing installed on the host):
- `venv35`: pyspark 3.5.9, sqlglot 30.23.0, sqlfluff 4.4.0, sparkmeasure 0.28.0, sqllineage 1.5.9, pydeequ 1.7.0
- `venv4`: pyspark 4.2.0 (+ pydeequ)

Spark SQL example (10 lines, local mode), `logs/preflight_explain.py` + `logs/preflight_explain_35.out`:
EXPLAIN FORMATTED and EXPLAIN COST both printed (BroadcastHashJoin plan, cost rows);
`ROWS: 50`. Spark UI port: 4040 (`spark.ui.port`), served while the app lives (later
verified live by the DataFlint probe reading `http://localhost:4040/`).
Event log: `spark.eventLog.enabled=true` writes `spark-events35/local-*` (2.1 MB single
file on 3.5.9; an `eventlog_v2_local-*` directory on 4.2.0 - relevant for the bank's
history-server config).

sqlglot probe (`logs/sqlglot_probe.out`): transpile spark->postgres and spark->databricks
OK; AST `Join` node reachable; erroneous query raises `ParseError: Expecting ). Line 1,
Col: 22` with the offending token highlighted.

## Step 1 - synthetic job with planted problems (`synthetic-job/synthetic_job.py`)

Planted truth (output in `logs/synthetic_job.out`, `logs/eventlog_truth.out`):
- small files: 60 parquet files, total 110.2 KB, avg 1.8 KB/file, read as 12 partitions
- skew: 96% of 4M rows have k=7; after `repartition(32,"k")` + heavy sha2 the reduce
  stage shows 32 tasks with min/median/max = 13/29/719 ms -> one task 25x the median

## Capability matrix (predeclared: tool x problem; found / missed / unsupported / untested)

"found" = the planted problem is visible in the tool's own output I ran and quote below.

| tool | skew | small files | plan/SQL diagnostics | install on Windows+Docker (exercised) |
|---|---|---|---|---|
| History Server (pip) | found (stage summary API: stage 17 numTasks=32, `logs/hs_stage17.json`; UI shows min/median/max summary; taskList endpoint not fetched this run) | unsupported (shows task count, not file sizes) | partial: SQL tab + plan from event log (documented; not fetched this run) | exercised via pip-pyspark sbin; docker path documented only |
| DataFlint 0.9.9 | untested at UI level: plugin attached and tab live (`logs/dataflint.out`: `DataFlint tab present: True`, tab `/dataflint/`); its skew heat map not screenshotted (headless run) | untested same way | same | exercised: Maven jar `io.dataflint:spark_2.12:0.9.9` resolved and plugin registered on driver |
| sparkMeasure 0.28.0 + jar 0.25 | found indirectly: per-stage rows show the 32-task stage taking 4009 ms executorRunTime of the job's 12 s (`logs/sparkmeasure_stagemetrics.json/`); aggregate mode prints NO per-task max/median, so the 25x outlier itself is not shown | missed (metrics are per stage/executor; file sizes invisible) | unsupported (not a plan tool) | exercised: pip wheel has NO jar - needs Maven `ch.cern.sparkmeasure:spark-measure_2.12:0.25`; offline banks must vendor it |
| event-log JSON (baseline) | found: 719 ms vs 29 ms median (`logs/eventlog_truth.out`, `logs/eventlog_truth.py` - 40 lines, no deps) | found only as file count/sizes at the source dir, not from the log | unsupported | exercised; runs anywhere python runs |
| sqlglot 30.23.0 | unsupported (static SQL) | unsupported | found: ParseError with position on broken SQL; transpile spark<->postgres/databricks/hive; column lineage `label` -> CTE -> `dim.label` (`logs/sqlglot_probe.out`, `logs/sqlglot_lineage.out`) | exercised: pure pip |
| sqlfluff 4.4.0 | unsupported | unsupported | found: 21 findings on planted queries incl. AM05 ambiguous join, RF02 unqualified refs + PRS parse errors (`logs/sqlfluff_lint.out`); dialect name is `sparksql` (spark3 renamed) | exercised: pure pip |
| sqllineage 1.5.9 | unsupported | unsupported | found: table lineage `dim`, `fact_smallfiles` extracted from the planted file; column level empty for SELECT-only statements (`logs/sqllineage.out`) | exercised: pure pip |
| pydeequ 1.7.0 | unsupported (data quality) | unsupported | unsupported | blocked: runs fail on both Spark 3.5.9-py3.11 and 4.2.0 with `py4j.Py4JException: Method iterableAsScalaIterable([class java.lang.String]) does not exist` (`logs/pydeequ.err`, `logs/pydeequ4.err`) |
| Sparklens 0.3.2 | untested (dormant: release 2020, Spark-2-era coords, Spark 3.5 compat undocumented - single source: README) | untested | untested | documented only |
| Great Expectations 1.24.0, Soda 4.27.0, Spline 1.0.0-RC3, dbt-spark, sqlcheck 1.3, Dr.Elephant | not run (time budget / out of matrix scope) | not run | sqlcheck: documented (Windows .exe exists) | documented only; see tools.tsv per tool |

## Inventory

`tools.tsv`: 16 rows x 10 columns (URL, licence, last release with date, what it does,
Windows+Docker install path, Linux/WSL-only notes, exercised flag). All release data
from GitHub/PyPI APIs or repo pages on 2026-10-18; every row carries its source URL.

Notable findings for the bank context:
1. The pip-only path (sqlglot, sqlfluff, sqllineage) is the only one with zero JVM /
   Maven dependencies - it works on any Windows box with just Python, no Docker needed.
2. sparkMeasure and DataFlint both resolve a jar from Maven Central at runtime; both
   wheels/repos allow vendoring the jar for offline use (URLs in
   `dockerfiles/Dockerfile.analysers`).
3. Soda Core / soda-sparkdf 4.27.0 now carries licence "Proprietary" on PyPI (single
   source: pypi.org JSON, 2026-10-13) - licence review before any bank use.
4. Dr. Elephant is dormant (last push 2023-08-22, not archived); Sparklens last release
   2020. Successors worth proposing: DataFlint (UI) and sparkMeasure (metrics).
5. Spark 4 writes `eventlog_v2_*` directories, not single files (observed here); a
   history-server config for the bank must match the Spark line it faces.

## Deliverables

- report.md (this file), tools.tsv, dockerfiles/ (3 files + README, all marked untested),
  synthetic-job/ (synthetic_job.py, sparkmeasure_run.py, dataflint_run.py, queries.sql,
  data/), logs/ (every output quoted above), decision.md, handoff.md, finished.

## Step -> evidence map (audit requirement)

- Step 0 preflight: every check -> table above with command + file under logs/.
  Partial: docker run hello-world blocked (daemon down); Spark UI port noted, UI
  screenshot not taken (headless).
- Step 1 inventory -> tools.tsv (16 tools, URL+licence+last release+install path each);
  run-what-runs -> capability matrix above (5 tools exercised end-to-end: History
  Server API, DataFlint plugin, sparkMeasure, sqlglot, sqlfluff, sqllineage = 6).
- Stop condition met: deliverables exist and every matrix row carries its evidence file.
- Not done / limits: pydeequ blocked (quoted error), Docker build/run untested (daemon
  down), DataFlint UI content and History Server taskList endpoint not fetched (plugin
  attach and stage summary API verified instead), Sparklens/GE/Soda/Spline/dbt/sqlcheck
  not executed (surveyed only), Windows-without-WSL operation not proven by any of the
  above (see assumption).

## Errata 2026-10-31 (2026-10-18 code review, approved by the owner)

The text above is preserved. Where it conflicts, this section wins.

- The heavy sha2 claim is withdrawn: Spark optimized the computation away. The stage outlier is real but does not validate this explanation. Docker/Windows and DataFlint integration remain unverified.
