# Key 07 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 007): see repro/outputs/007-*.txt.

## Required findings (any one term suffices per line)
```required_findings
LIMIT without ORDER BY
nondeterministic | arbitrary rows
```

## Decoys (count as false claims if reported as defects)
```non_defects
200 rows being sampled is fine
the % 7 expression is not the defect
```

## Expected fix
Add a deterministic ORDER BY (unique key) before LIMIT.

## How to check the fix by running
flaw.sql run twice under different repartitioning returns different id sets (see verification log); fixed.sql always 0-4.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 07 (from cases/).
