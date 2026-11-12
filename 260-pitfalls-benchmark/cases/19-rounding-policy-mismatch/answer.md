# Key 19 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 019): see repro/outputs/019-*.txt.

## Required findings (any one term suffices per line)
```required_findings
HALF_UP
HALF_EVEN | banker
bround
```

## Decoys (count as false claims if reported as defects)
```non_defects
round(2.5)=3 alone is not a bug — the mismatch of policies is
```

## Expected fix
Pin one rounding policy across systems: BROUND (HALF_EVEN) where the other system uses banker's rounding, and document it.

## How to check the fix by running
flaw.sql total=7; fixed.sql total=6.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 19 (from cases/).
