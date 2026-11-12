# Key 31 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 031): see repro/outputs/031-*.txt.

## Required findings (any one term suffices per line)
```required_findings
inferSchema turns leading-zero codes into INT
codes corrupted before the join
schema must be explicit
```

## Decoys (count as false claims if reported as defects)
```non_defects
CSV with header=True is fine
the dimension table itself is correct
```

## Expected fix
Pass an explicit schema (code STRING, name STRING) instead of inferSchema for code-like columns (see repro/outputs/031).

## How to check the fix by running
df variants: the inferSchema read reports code:int and values [1, 2, 10] (join with '001' impossible); the explicit-schema read keeps ['001','002','010'] and joins to the dim.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 31 (from cases/).
