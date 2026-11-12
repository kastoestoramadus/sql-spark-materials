# Key 05 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 005): see repro/outputs/005-*.txt.

## Required findings (any one term suffices per line)
```required_findings
WHERE on right table
outer join became inner
unmatched rows lost
```

## Decoys (count as false claims if reported as defects)
```non_defects
putting the s.status filter into the ON clause is the fix, not a new bug
the LEFT keyword itself is fine
```

## Expected fix
Move right-side predicates from WHERE into the ON clause (or pre-filter the right table).

## How to check the fix by running
flaw.sql returns 1 row (id 1); fixed.sql returns 2 rows (id 2 with NULL status).
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 05 (from cases/).
