# Handoff - task 230 (attempt 1, worker 8 of batch 2)

## Done

- Preflight (Step 0) fully recorded: network 4x200, Corretto 17.0.15, python 3.13.16
  (venvs on 3.11.17), uv 0.13.1, docker.exe 24.0.7 with daemon down; venvs
  `venv35`/`venv4` (pyspark 3.5.9 / 4.2.0, sqlglot 30.23.0, sqlfluff 4.4.0,
  sparkmeasure 0.28.0, sqllineage 1.5.9, pydeequ 1.7.0) with `UV_CACHE_DIR` and
  `.ivy2` inside `R=` the results dir; Spark SQL EXPLAIN FORMATTED/COST outputs kept
  (`logs/preflight_explain_35.out`, `logs/preflight_explain_4.out`); event log v1 file
  (3.5.9) vs v2 dir (4.2.0) observed; sqlglot transpile/ParseError probe.
- Synthetic job `synthetic-job/synthetic_job.py`: planted skew (96% hot key, reduce
  stage 32 tasks, one 719 ms vs 29 ms median) and small files (60 parquet, avg 1.8 KB);
  planted-truth extractor `logs/eventlog_truth.py` (stdlib-only, reusable).
- Tools exercised: sparkMeasure (needs Maven jar; per-stage JSON export), DataFlint
  0.9.9 plugin (Maven; `/dataflint/` UI tab verified live), History Server from pip
  pyspark (API: app list + stage 17 summary), sqlfluff (`sparksql` dialect, 21
  findings), sqlglot (transpile/AST/lineage), sqllineage (table lineage). All outputs
  under `logs/`.
- `tools.tsv` (16 tools, URL/licence/last-release/install-path), `dockerfiles/`
  (analysers image, history-server+DataFlint image, compose - all marked UNTESTED
  with offline-jar URLs), `report.md` with the predeclared capability matrix, and
  `decision.md` (recommendation: sqlglot + sparkMeasure + DataFlint, sqlfluff as
  cheap fourth; medium-high confidence).
- No branch/worktree (results dir only, as the task allows). No commits, no pushes,
  nothing outside the results dir was written.

## Not done

- Docker build/run of anything: Docker Desktop daemon was down
  ("open //./pipe/docker_engine: The system cannot find the file specified");
  all three dockerfiles are untested.
- pydeequ: analysis run failed on BOTH matrices (3.5.9+deequ 2.0.21-spark-3.5 and
  4.2.0+deequ 2.0.18-spark-4.1) with `py4j.Py4JException: Method
  iterableAsScalaIterable([class java.lang.String]) does not exist`
  (`logs/pydeequ.err`, `logs/pydeequ4.err`); suspect a pydeequ/Scala-version call
  into the JVM (needs upstream issue check or a deequ-jar version matrix).
- DataFlint's actual UI content (heat map/skew view) not screenshotted: headless run
  verified only plugin registration and tab presence.
- History Server `/stages/17/0/taskList` endpoint not fetched (stage summary only).
- Great Expectations, Soda, Spline, dbt-spark, sqlcheck, Sparklens: surveyed only,
  never executed.
- Windows-without-WSL operation of anything: not proven (see report assumption).

## Proposals needing a decision

1. Adopt the toolbox order from decision.md (sqlglot, sparkMeasure, DataFlint; add
   sqlfluff for lint). Risk: DataFlint needs Maven/vendor path at the bank.
   Recommendation: yes, plus vendor the three jars listed in
   `dockerfiles/Dockerfile.analysers`.
2. If Docker Desktop can be started on the Windows host, build and smoke-test
   `dockerfiles/docker-compose.yml` (exact commands are in the compose file's
   comments). Risk: none beyond local container use. Recommendation: do it before
   the first bank session.
3. pydeequ root-cause: file an upstream issue or pin a working combination.
   Risk: low (analysis only). Recommendation: check awslabs/python-deequ issues for
   "iterableAsScalaIterable" first.

## Ready-made texts

None needed (no PR or issue is part of this task).

## Verification

- Every capability-matrix row points at a file under `logs/` produced by a run this
  attempt; commands and failures are in `commands.log`; claim-falsification list at
  the end of `progress.md` (5 claims, each with the attempted refutation).
- Versions/licences in `tools.tsv` from GitHub API / PyPI JSON / repo pages, all
  fetched 2026-10-18 (URLs in the file).
- Identity block in `report.md`; `finished` created last.

## Unverified

- soda-sparkdf "Proprietary" licence (single source: PyPI licence field 2026-10-13;
  their LICENCE file not read).
- Sparklens on Spark 3.5 (README shows Spark-2-era coordinates; no run).
- Not searched: Docker Hub mirror feasibility at banks; Databricks/EMR/Synapse docs
  for skew tooling (cloud-platform specifics); DataFlint history-server install doc
  page beyond the README; GE 1.24 Spark datasource doc page (docs URL 404ed);
  Windows-native pyspark caveats (winutils.exe etc. - irrelevant inside Docker);
  no search of vendor blogs or paid tool comparisons (not in scope).
- No prompt-injection attempts were found in fetched content.
