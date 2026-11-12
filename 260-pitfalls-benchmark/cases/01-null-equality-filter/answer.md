# Key 01 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 001): see repro/outputs/001-*.txt.

## Required findings (any one term suffices per line)
```required_findings
note = NULL
NULL comparison
UNKNOWN
```

## Decoys (count as false claims if reported as defects)
```non_defects
rows with id 1 and 3 are correctly excluded
IS NOT NULL
```

## Expected fix
Replace = NULL with IS NULL (= NULL is never TRUE).

## How to check the fix by running
flaw.sql returns 0 rows; fixed.sql returns [(2,)].
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 01 (from cases/).
