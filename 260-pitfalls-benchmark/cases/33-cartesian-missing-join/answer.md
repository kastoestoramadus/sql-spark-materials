# Key 33 (HIDDEN FROM REVIEWER)

Defect (category: cost, from pitfall 033): see repro/outputs/033-*.txt.

## Required findings (any one term suffices per line)
```required_findings
cartesian
missing join condition
row count multiplies
```

## Decoys (count as false claims if reported as defects)
```non_defects
filtering grp=1 first is a valid optimisation, not the defect
```

## Expected fix
Add the join predicate (a.id = b.id); check the plan for CartesianProduct.

## How to check the fix by running
flaw.sql returns 100*14=1400 rows counted; fixed.sql returns 14; plan shows CartesianProduct vs SortMergeJoin/ShuffledHashJoin.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 33 (from cases/).
