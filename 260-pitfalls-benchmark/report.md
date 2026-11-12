# Report — task 260 SQL/Spark pitfalls + benchmark (attempts 1-2)

Executed by: glm-5.3/xh; effort: xh; ZCode idle subagent
Coordinator/run: coordinator model id: account:zai-offpeak-idle-plan/GLM-5.3; effort: unknown, form default; harness: ZCode idle turn; task 260-sql-spark-pitfalls-and-benchmark; attempt 2; worker 1 of batch 4
Start: 2026-10-18T20:26:18+02:00  End: 2026-10-19T19:03:00+02:00

Attempts 1 (glm-5.3/xh, worker 9 of batch 3) and 2 (this worker) are one body of work. Attempt 1
produced the 35 pitfalls, 27 verified cases, local-first.md, score.py, README, decision.md; attempt 2
built and verified the remaining 13 cases (40/40), corrected pitfall 020 and case 20 to match what
the runs show, and ran TPC-H sf=0.1 locally. Everything below carries run evidence; source URLs are
reference pointers, not fetched quotes.

Assumption (conservative reading): "at least 30 pitfalls" = 30 entries each verified by an actual
run in this environment (wrong and right shown), not collected from docs. All data is synthetic;
no bank data exists in these files.

## Result in one paragraph
35 pitfalls reproduced on Spark 4.2.0 local mode (+ pyspark 3.5.1, DuckDB 1.5.6, sqlite 3.54.0,
all in results-dir venvs), all 40 benchmark cases built and verified with hidden keys, decoys and
run-proven oracles (correctness 33, performance 3, cost 3, maintainability 1; difficulty 15/15/10),
a scorer (score.py), a measured local scale-trend experiment, a measured TPC-H sf=0.1 local run with
a DuckDB-vs-Spark differential oracle, a local-first recipe (Windows+Docker, no WSL needed), and
decision.md. Remaining gaps: no real reviewer-model runs (idle-pool rule), mypy --strict not run,
case 25's oracle still weak (labelled), TPC-DS not run.

## Step -> evidence map
- Part 1, >=30 pitfalls reproduced locally: DONE (35) — pitfalls.tsv (35 rows, each cites
  repro/outputs/NNN-*.txt with the run output; category, wrong/right, why, detect static, detect
  test, lint-vs-data column). Categories cover the task list: NULL semantics (001-003),
  joins (004, 005, 033), fan-out, WHERE-vs-ON, time zones (025, 026, 027, 028), decimal
  precision/rounding (018, 019), integer overflow (020), implicit casts / ANSI Spark3-vs-4
  (021-024, cross files), default window frames (010, 011), nondeterministic functions/ordering
  (007, 008, 009, 013), LIMIT w/o ORDER BY, string collation/case (029, 030, 035), float
  aggregation order (017), distinct vs group by (014), date arithmetic (028), case sensitivity
  (030), ETL/csv (031), LIKE injection (032), set-ops multiplicity (015, 016), partial sort (034).
- Part 1, "which can be found by parser-level lint vs need data": DONE — pitfalls.tsv column
  lint_only (12 lint-able, 23 need data/stats).
- Part 2, local-first strategy with runs: DONE minus TPC-DS — local-first.md (recipe incl. Dockerfile,
  distribution-preserving golden-set rules, plan/result goldens, DuckDB differential with the
  alignment checklist, cluster-mimicking config, honest cannot-reproduce list) + measured scale
  trend (repro/outputs/scale-trend.tsv) + measured TPC-H sf=0.1 in local mode with the revenue sum
  matching across DuckDB and Spark (repro/tpch/tpch-run.txt, quoted in local-first.md section 6).
  TPC-DS (dsdgen compile route) not run.
- Part 3, 40 cases: DONE — 40 built and verified (cases/, verification-log.md regenerated for all
  40 with plan.txt; each case: gen.sql, flaw.sql, fixed.sql, plan.txt, prompt.md, answer.md with
  required_findings + decoys, case.json). Difficulty 15 easy / 15 medium / 10 hard (target met).
  New in attempt 2: pitfalls 009 (dropDuplicates arbitrary survivor, oracle: two partition-local
  sorts pick different survivors), 013 (unseeded rand: 1031 vs 981, seeded 1029=1029), 018, 020,
  021, 024 (ANSI df-variants toggle both modes), 031 (inferSchema int vs explicit-schema string,
  data.csv in the case dir), 035; plus 5 perf/cost cases with structural oracles: 36 (shuffle
  partitions 200 vs 8 via forced Exchange, AQE interplay shown), 37 (payload columns in flaw plan=2,
  fixed=0), 38 (repartition 100 vs coalesce 1), 39 (auto-broadcast floats with stats; SMJ under
  threshold=-1 while the hint still broadcasts), 40 (collect 100k rows 437-2526 ms vs agg 43-194 ms).
  Weak oracles still labelled: case 25 (epoch evidence in pitfall 025), case 34 (within-tie order).
- score.py: DONE (substring matching on key phrasings, decoy penalty, per-difficulty recall);
  NOT exercised against a real model submission (no model CLIs allowed in idle pool).
- README.md: DONE (counts updated to 40; how to run reviewers, with/without skill, how to compare).
- decision.md: DONE (evidence table E1-E7, options, recommendations with confidence, owner-only
  items; TPC-H note updated).
- verification-log.md: DONE for all 40 cases (defect shows, fix fixes; variants for 07/08/17/25/26;
  cases 20/21/24 show both ANSI modes; long row lists truncated to first 3 + count for readability).

## Not done (with causes)
- Real reviewer-model runs over the benchmark (idle pool forbids starting other model CLIs; README
  gives the loop for the owner). score.py untested against a real submission.
- TPC-DS generation (compile-in-container route; only the recipe, not a run).
- mypy --strict on score.py/verify_all.py/scale_run2.py/build_cases.py: not run (time; annotations
  present).
- Case 25 oracle redesign to epoch comparison: not done (labelled weak in its answer.md; pitfall 025
  carries the epoch evidence).
- Source URLs not fetched/verified in either attempt; behavioral claims rest on run evidence.

## Key findings worth the owner's attention
1. Spark 4.2.0 defaults spark.sql.ansi.enabled=TRUE, Spark 3.5.1 defaults FALSE (fresh-session
   probes, repro/outputs/000-cross-spark{3,4}.txt). Upgrading flips CAST('abc' AS INT) from silent
   NULL to an exception, 1/0 from NULL to exception. For a bank audit this is the first config to
   check. On a fixed 14-statement list the two versions are otherwise identical (diff = error
   wording only).
2. Attempt-2 correction: non-ANSI INT addition does NOT return NULL — it wraps (INT_MAX+1 ->
   -2147483648, verification-log.md case 20 df variant and repro/outputs/020). pitfall 020's TSV row
   and the case key now say wraparound; the earlier "NULL silently" wording came from docs, not runs.
   Same correction family as attempt 1's DECIMAL-overflow refutation: overflow behaviour differs by
   type and mode; check by running.
3. Plan-shape oracles beat timing oracles locally: on local[1], tiny GROUP BY plans need no Exchange
   at all (single input split), AQE coalesces forced shuffles, and auto-broadcast picks
   BroadcastHashJoin even for a stats-underestimated 15 MB dimension (cases 36, 39). Perf cases
   therefore pin config or grep plan nodes; wall-clock stays a secondary signal.
4. DuckDB 1/0 = inf (not NULL), sqlite CAST('abc' AS INT)=0, sqlite LIKE is case-insensitive:
   three engines, three policies (outputs 021/022/035) — differential testing needs semantic
   alignment first. Also ANSI-to_timestamp: a wrong datetime pattern throws CANNOT_PARSE_TIMESTAMP
   on Spark 4.2 default and silently NULLs on 3.x semantics (case 27).
5. Local scale runs: broadcast joins show no fact-side shuffle at any scale, and JVM warm-up
   noise exceeds the 10k->1M wall-time trend — plan shape and shuffle records are the reliable
   local signals, seconds are not (local-first.md section 4). TPC-H sf=0.1: dbgen 1.2 s,
   Spark read+agg 3.9 s, revenue identical across engines (local-first.md section 6).

## Files
report.md, pitfalls.tsv, repro/ (run_all.py, pitfalls_core.py, pitfalls_more.py, common.py,
cross_version.py, scale_run.py, scale_run2.py, make_tsv.py, tpch/, outputs/), local-first.md,
cases/ (build_cases.py, verify_all.py, 40 case dirs), score.py, README.md, verification-log.md,
decision.md, progress.md, checkpoint.md, commands.log, handoff.md.
