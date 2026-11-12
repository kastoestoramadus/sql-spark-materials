# Key 04 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 004): see repro/outputs/004-*.txt.

## Required findings (any one term suffices per line)
```required_findings
duplicate key
fan-out
SUM inflated | double count
```

## Decoys (count as false claims if reported as defects)
```non_defects
the fact table rows themselves are unique
GROUP BY acct alone would not fix it
```

## Expected fix
Deduplicate dimension keys (SELECT DISTINCT) before aggregating; add uniqueness tests on keys.

## How to check the fix by running
flaw.sql total=60; fixed.sql total=30.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 04 (from cases/).
