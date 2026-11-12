# Key 22 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 022): see repro/outputs/022-*.txt.

## Required findings (any one term suffices per line)
```required_findings
CAST returns NULL
unparseable
rows silently dropped
```

## Decoys (count as false claims if reported as defects)
```non_defects
the NULL row being excluded is ordinary NULL semantics, not the cast defect
```

## Expected fix
Use TRY_CAST plus an explicit audit/count of parse failures; decide a policy for dirty values.

## How to check the fix by running
flaw.sql under ansi=false returns only '12' silently (rows lost); under Spark 4 default (ansi=true) it throws CAST_INVALID_INPUT; fixed.sql (TRY_CAST) returns '12' and the dirty value is countable via TRY_CAST IS NULL AND s IS NOT NULL.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 22 (from cases/).
