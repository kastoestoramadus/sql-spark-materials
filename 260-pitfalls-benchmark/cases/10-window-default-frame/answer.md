# Key 10 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 010): see repro/outputs/010-*.txt.

## Required findings (any one term suffices per line)
```required_findings
RANGE frame
ties | peers
running total includes peers
```

## Decoys (count as false claims if reported as defects)
```non_defects
PARTITION BY acct is correct
final ORDER BY evt, amt in the outer query is fine
```

## Expected fix
Add an explicit ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW frame, or make the ORDER BY unique (evt, seq).

## How to check the fix by running
flaw.sql: both evt=2 rows show running=80; fixed.sql: 30 then 80.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 10 (from cases/).
