# Key 15 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 015): see repro/outputs/015-*.txt.

## Required findings (any one term suffices per line)
```required_findings
UNION without ALL
implicit DISTINCT
duplicates removed
```

## Decoys (count as false claims if reported as defects)
```non_defects
the individual id values are correct
UNION ALL being cheaper is a bonus, not the defect
```

## Expected fix
Use UNION ALL when duplicates are meaningful (or dedupe deliberately at one place).

## How to check the fix by running
flaw.sql counts 3; fixed.sql counts 6.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 15 (from cases/).
