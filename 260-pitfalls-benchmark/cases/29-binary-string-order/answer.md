# Key 29 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 029): see repro/outputs/029-*.txt.

## Required findings (any one term suffices per line)
```required_findings
binary | codepoint ordering
uppercase sorts first
collation
```

## Decoys (count as false claims if reported as defects)
```non_defects
the three names are all valid data
LIMIT 1 here is legitimate because ORDER BY is total under a collation
```

## Expected fix
Use an explicit COLLATE (Spark 4 collation) or a normalised sort-key column; document that default order is binary.

## How to check the fix by running
flaw.sql returns 'Zebra'; fixed.sql returns 'apple' under case-insensitive Unicode collation.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 29 (from cases/).
