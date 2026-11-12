# Key 28 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 028): see repro/outputs/028-*.txt.

## Required findings (any one term suffices per line)
```required_findings
fixed 31-day month assumption
skips February
INTERVAL 1 MONTH clamps
```

## Decoys (count as false claims if reported as defects)
```non_defects
the date literal being end-of-month is not itself a defect
datediff is not used here
```

## Expected fix
Use INTERVAL 1 MONTH (clamps to month end) or an explicit business rule for day>=29.

## How to check the fix by running
flaw.sql returns 2026-03-03; fixed.sql returns 2026-02-28.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 28 (from cases/).
