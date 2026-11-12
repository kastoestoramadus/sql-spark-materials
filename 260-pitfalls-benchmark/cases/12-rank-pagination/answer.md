# Key 12 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 012): see repro/outputs/012-*.txt.

## Required findings (any one term suffices per line)
```required_findings
RANK
ties
gap | position
```

## Decoys (count as false claims if reported as defects)
```non_defects
ROW_NUMBER would give exactly 2 rows but loses tie information — a policy choice, not a defect
```

## Expected fix
Pick the ranking policy explicitly: DENSE_RANK for no position gaps, or ROW_NUMBER with a documented tie-break.

## How to check the fix by running
flaw.sql returns 3 players (a,b,c); fixed.sql returns 3 players but the next page continues at 3 (no skipped position).
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 12 (from cases/).
