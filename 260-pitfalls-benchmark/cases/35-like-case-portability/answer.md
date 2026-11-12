# Key 35 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 035): see repro/outputs/035-*.txt.

## Required findings (any one term suffices per line)
```required_findings
LIKE is case-sensitive in Spark
porting from sqlite | MySQL changes the result set
```

## Decoys (count as false claims if reported as defects)
```non_defects
filtering to a-prefix fruits is the goal
Banana is correctly excluded
```

## Expected fix
Normalise both sides (lower(fruit) LIKE 'a%') or use an explicit collation, so the predicate means the same thing on every engine (see repro/outputs/035 for the sqlite/DuckDB comparison).

## How to check the fix by running
flaw.sql returns 2 rows (apple, apricot); fixed.sql returns 3 (Apple, apple, apricot).
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 35 (from cases/).
