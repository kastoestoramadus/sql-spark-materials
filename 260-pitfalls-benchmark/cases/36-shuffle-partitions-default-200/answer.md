# Key 36 (HIDDEN FROM REVIEWER)

Defect (category: performance, from pitfall -): see repro/outputs/--*.txt.

## Required findings (any one term suffices per line)
```required_findings
default 200 shuffle partitions for 10k rows
199 nearly-empty tasks per stage
spark.sql.shuffle.partitions not sized
AQE coalescing not verified
```

## Decoys (count as false claims if reported as defects)
```non_defects
GROUP BY k is the right shape
50 groups is not the problem
```

## Expected fix
Size spark.sql.shuffle.partitions to the data (single digits for 10k rows) or rely on AQE coalescing deliberately, after checking it is on; keep 200 only when the upstream shuffle is big.

## How to check the fix by running
df variants: with AQE off and the default 200, a hash shuffle of q36 (repartition by k) yields 200 partitions of ~50 rows; setting 8 yields 8. With AQE ON (the default) the same shuffle is coalesced to 1 output partition - observed - but the 200 shuffle blocks are still written first. Also note: on this local[1] session the tiny GROUP BY plan needs no Exchange at all (single input split).
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 36 (from cases/).
