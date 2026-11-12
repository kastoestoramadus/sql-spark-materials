---
name: spark-skew-check
description: Use when a Spark event log is available (spark.eventLog.enabled=true) and the question is about slow stages, skew, spill or partition sizing; also to verify that an optimisation actually helped by comparing before/after logs. Produces per-stage task-time statistics with a SKEW flag; pure Python, no JVM.
---

# Spark skew check

## When to use
- A stage is slow and the static plan looks fine (skew is invisible in EXPLAIN - task 220 case q05: plan
  normal, event log showed max/median 17.1 on stage 7).
- After a change (salting, repartition, AQE) to verify the improvement with the same summary.

## Steps
1. Get the event log file (`.inprogress` fine) onto the review machine; point the script at file or dir:
   `python scripts/eventlog_summary.py <eventlog-file-or-dir>`
2. Output: one row per stage: `stage tasks median_ms p90_ms max_ms skew(max/median) name`;
   SKEW flag when max/median > 5 AND max > 1s.
3. Read the flagged stages' names and match them to plan operators (Exchange hashpartitioning key);
   the join/aggregation key causing the skew is the one partitioning that stage.
4. Report only measured numbers: "stage 7: 200 tasks, median 15 ms, max 256 ms, ratio 17.1" (own run
   2026-10-18) - not adjectives.
5. Compare before/after by running the script on both logs and putting the rows side by side.

## Validated behaviour
Detected a planted 80%-single-key skew (task 220 q05) in a 2.8 MB local event log; SQL executions with
plans in the same log were also counted (16 in the run).

## Blind spots
- Ratio on very short tasks is noisy (the 1 s floor exists for that reason); with fewer than ~10 tasks the
  p90 falls back to max.
- Event-log JSON schema varies between Spark minor versions; unknown fields are ignored, missing fields
  yield empty rows - if a row looks empty, check the Spark version before trusting the summary.

## Privacy
Event logs contain table paths, SQL text and user names: they stay on the machine with the query text.
