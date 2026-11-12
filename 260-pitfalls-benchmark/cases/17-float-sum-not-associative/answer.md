# Key 17 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 017): see repro/outputs/017-*.txt.

## Required findings (any one term suffices per line)
```required_findings
floating point
order of summation | partitioning
not associative
```

## Decoys (count as false claims if reported as defects)
```non_defects
DuckDB or another engine returning a different value is not a Spark bug — same non-associativity
```

## Expected fix
Aggregate in DECIMAL (or integer cents) for money, or compare with a tolerance, never exact equality on DOUBLE sums.

## How to check the fix by running
SUM over the 4 values yields 1.0 in 1 partition and 2.0 in 2 partitions (see verification log); DECIMAL fixed path is exact.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 17 (from cases/).
