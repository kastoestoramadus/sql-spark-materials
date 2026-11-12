# Key 02 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 002): see repro/outputs/002-*.txt.

## Required findings (any one term suffices per line)
```required_findings
NOT IN
NULL in subquery
no rows returned
```

## Decoys (count as false claims if reported as defects)
```non_defects
the deny value 2 correctly removes id 2
IN (without NOT) would behave differently
```

## Expected fix
Filter NULLs out of the subquery or use LEFT ANTI JOIN.

## How to check the fix by running
flaw.sql returns 0 rows; fixed.sql returns [(1,),(3,)].
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 02 (from cases/).
