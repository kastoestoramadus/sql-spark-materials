# Key 06 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 006): see repro/outputs/006-*.txt.

## Required findings (any one term suffices per line)
```required_findings
COUNT(col) skips NULL
SUM of all-NULL is NULL
COALESCE
```

## Decoys (count as false claims if reported as defects)
```non_defects
dept 'a' having one non-NULL bonus counted is correct
ORDER BY dept is fine
```

## Expected fix
Decide explicitly: COUNT(*) for rows, COUNT(col) for non-NULL values, COALESCE(SUM(...),0) for totals.

## How to check the fix by running
flaw.sql: b shows 0 rows_with_bonus and NULL total; fixed.sql: b shows 1 row and 0.0 total.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 06 (from cases/).
