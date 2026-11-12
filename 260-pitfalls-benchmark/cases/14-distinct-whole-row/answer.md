# Key 14 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 014): see repro/outputs/014-*.txt.

## Required findings (any one term suffices per line)
```required_findings
DISTINCT applies to whole row
extra column
two rows for a=1
```

## Decoys (count as false claims if reported as defects)
```non_defects
(2,'z') appearing once is correct
ORDER BY a,b is not the issue
```

## Expected fix
Project only the key you deduplicate on (GROUP BY a / DISTINCT a).

## How to check the fix by running
flaw.sql returns 3 rows; fixed.sql returns 2 rows.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 14 (from cases/).
