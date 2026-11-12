# Key 30 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 030): see repro/outputs/030-*.txt.

## Required findings (any one term suffices per line)
```required_findings
case-sensitive
join drops matches
lower()
```

## Decoys (count as false claims if reported as defects)
```non_defects
the amounts and groups are irrelevant
NULL names are not involved here
```

## Expected fix
Normalize key casing (lower/initcap) on both sides before joining.

## How to check the fix by running
flaw.sql returns 0; fixed.sql returns 2.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 30 (from cases/).
