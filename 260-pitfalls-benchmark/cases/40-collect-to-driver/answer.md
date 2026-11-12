# Key 40 (HIDDEN FROM REVIEWER)

Defect (category: cost, from pitfall -): see repro/outputs/--*.txt.

## Required findings (any one term suffices per line)
```required_findings
collect() pulls all rows to the driver
aggregation done in Python instead of the engine
driver memory and serialization cost
```

## Decoys (count as false claims if reported as defects)
```non_defects
summing id is a fine goal
100k rows is not the issue at this scale - the pattern is
```

## Expected fix
Push the aggregation into Spark (agg(F.sum('id'))) and collect only the result row; collect() only small, bounded results.

## How to check the fix by running
df variants print (row count, milliseconds): collect()+Python loop vs a single aggregate - on this local[1] session the collect variant takes a multiple of the aggregate's time and both timings are single-run observations, not a cluster claim.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 40 (from cases/).
