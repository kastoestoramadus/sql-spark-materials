# Key 23 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 023): see repro/outputs/023-*.txt.

## Required findings (any one term suffices per line)
```required_findings
implicit cast of string to int
unparseable becomes NULL
silent row loss
```

## Decoys (count as false claims if reported as defects)
```non_defects
'0010' matching 10 is correct cast behaviour, not a bug
the ORDER BY is irrelevant
```

## Expected fix
Compare with an explicit TRY_CAST (and audit NULL casts), or cast the literal to string when the key is a string.

## How to check the fix by running
flaw.sql: ansi=false -> (' 10 ','0010','10') with 'abc' silently dropped; Spark 4.2 default (ansi=true) -> CAST_INVALID_INPUT error; fixed.sql shows every value with its cast key.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 23 (from cases/).
