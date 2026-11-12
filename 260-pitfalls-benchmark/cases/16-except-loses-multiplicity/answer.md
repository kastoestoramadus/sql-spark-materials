# Key 16 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 016): see repro/outputs/016-*.txt.

## Required findings (any one term suffices per line)
```required_findings
EXCEPT DISTINCT
multiplicity | duplicates removed
set semantics
```

## Decoys (count as false claims if reported as defects)
```non_defects
value 2 being removed is correct
INTERSECT is not involved
```

## Expected fix
Use EXCEPT ALL when duplicates are meaningful, or aggregate with counts.

## How to check the fix by running
flaw.sql returns 1 row (one 1); fixed.sql returns 2 rows (1,1).
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 16 (from cases/).
