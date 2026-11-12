# Key 03 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 003): see repro/outputs/003-*.txt.

## Required findings (any one term suffices per line)
```required_findings
NULL join key
rows dropped
null-safe equality | <=>
```

## Decoys (count as false claims if reported as defects)
```non_defects
row (1,'a') matching is correct
an INNER join itself is not the defect
```

## Expected fix
Use null-safe equality <=> if NULL keys must match, or clean NULLs first by policy.

## How to check the fix by running
flaw.sql returns 1 row; fixed.sql returns 2 rows.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 03 (from cases/).
