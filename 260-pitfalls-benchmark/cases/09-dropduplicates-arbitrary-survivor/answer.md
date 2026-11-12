# Key 09 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 009): see repro/outputs/009-*.txt.

## Required findings (any one term suffices per line)
```required_findings
dropDuplicates keeps an arbitrary row
which duplicate survives is not defined
no ordering rule
```

## Decoys (count as false claims if reported as defects)
```non_defects
keeping one row per id is the goal itself
repartition(1) in the variants only exposes the order dependence
```

## Expected fix
State the winner explicitly: row_number() OVER (PARTITION BY id ORDER BY ts DESC) = 1, or max_by/argmax aggregation.

## How to check the fix by running
The two df variants sort the same data differently before dropDuplicates and get different payloads for id=1 ('old' vs 'new'); fixed.sql always returns 'new' (latest ts).
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 09 (from cases/).
