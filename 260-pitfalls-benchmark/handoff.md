# handoff.md — task 260, attempt 2 (final)

## Done
- All 40 benchmark cases built and verified (attempt 1: 27; attempt 2 added 09, 13, 18, 20, 21,
  24, 31, 35 from pitfalls + 5 perf/cost cases 36-40). Difficulty 15/15/10; categories 33
  correctness / 3 performance / 3 cost / 1 maintainability. Files per case: gen.sql, flaw.sql,
  fixed.sql, plan.txt, prompt.md, answer.md, case.json (+ data.csv for case 31).
- verification-log.md regenerated for all 40 (row lists >5 truncated to first 3 + count);
  attempt-1 rerun sections for cases 17/22/27 appended back from verification-log-partial-*.md.
  Oracles run-proven, including: 09 (partition-local sort asc keeps 'old', desc keeps 'new'),
  13 (unseeded 1031 vs 981; seeded 1029 = 1029), 20/21/24 (both ANSI modes via conf toggles),
  31 (inferSchema code:int 1,2,10 vs explicit schema '001','002','010'), 36 (forced Exchange
  200 vs 8 with AQE off; AQE coalesces to 1), 37 (payload_j plan lines 2 vs 0), 38 (100 vs 1
  partitions), 39 (SMJ only with autoBroadcastJoinThreshold=-1; hint always BHJ), 40 (collect
  100k rows 437-2526 ms vs aggregate 43-194 ms).
- Pitfall 020 corrected after running: non-ANSI INT add WRAPS (INT_MAX+1 -> -2147483648), it does
  not return NULL. pitfalls.tsv row 020 and case 20's key now match the evidence.
- TPC-H sf=0.1 measured locally: DuckDB tpch-extension dbgen 1.2 s (lineitem 600,572 rows),
  Spark 4.2 local read+agg 3.9 s, revenue 727877126573.30 identical across engines
  (repro/tpch/tpch-run.txt; local-first.md section 6 updated from recipe to result).
- README.md (40-case counts), report.md (attempt-2 identity block, step->evidence map, corrected
  category counts), decision.md (40 cases; TPC-H measured) updated.

## Not done
- Real reviewer-model runs over the benchmark (idle-pool rule forbids starting model CLIs);
  score.py therefore untested against a real submission.
- TPC-DS (dsdgen compile-in-container route): recipe only, not run.
- mypy --strict on score.py / verify_all.py / build_cases.py / scale_run2.py: not run (time).
- Case 25 oracle redesign to epoch comparison: still the weak count-comparison oracle, labelled
  in its answer.md; pitfall 025 carries the epoch evidence.
- Source URLs in pitfalls.tsv remain reference pointers (no page fetched in either attempt);
  behavioral claims rest on run evidence.

## Proposals needing a decision
- Strip answer.md/case.json before any benchmark bundle leaves this directory (keys inside).
  Risk if ignored: leaked keys invalidate the benchmark. Recommendation: do it at packaging time.
- Add a caution line to prompt.md generation for perf cases 36-39 telling the reviewer that
  plan.txt was produced on local[1] (single split, AQE on) so plan shapes there can differ from
  the story data; low risk, contained in build_cases.py.

## Ready-made texts
- None needed (no PR/issue work; results dir only).

## Verification
- cd cases && ../venv/py4/bin/python build_cases.py -> "built 40 cases"; ../venv/py4/bin/python
  verify_all.py -> exit 0, "wrote ../verification-log.md; cases: 40" (three full runs during
  oracle fixing; final 18:59 run).
- Counts rechecked from case.json files: easy 15 / medium 15 / hard 10; 40 case dirs.
- repro/tpch/tpch-run.txt: "duckdb dbgen sf=0.1 + parquet export: 1.2s; lineitem rows: 600572
  revenue: 727877126573.30" and "spark 4.2 local read+agg: rows=600572 revenue=727877126573.30
  wall=3.9s spark=4.2.0".
- Falsification passes recorded in progress.md (C7 shuffle-partition oracle, C8 auto-broadcast,
  C9 non-ANSI overflow NULL-claim: all refuted by runs and corrected in the deliverables).

## Unverified
- Cluster-only claims (local-first.md section 7): architectural reasoning, not measured.
- Fetched-page quotes: no source page fetched in either attempt; URLs are pointers.
- Not searched: Spark JIRA/PRs for ANSI-default history; ICU collation details; bank-specific
  Spark distributions (Databricks/EMR configs); Windows Docker Desktop specifics; TPC-DS tooling.
- The 437 ms vs 43 ms case-40 timing is single-run local[1] observation (earlier run 2526 vs 194);
  direction stable, magnitudes noisy — treated as secondary to the structural mechanism.
