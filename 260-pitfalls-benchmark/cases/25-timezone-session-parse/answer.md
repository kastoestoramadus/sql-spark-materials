# Key 25 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 025): see repro/outputs/025-*.txt.

## Required findings (any one term suffices per line)
```required_findings
session time zone
to_timestamp without zone
epoch differs
```

## Decoys (count as false claims if reported as defects)
```non_defects
the cutoff being an epoch number is fine; only the parsing side is ambiguous
```

## Expected fix
Parse with an explicit offset: CAST(concat(ts,'+00:00') AS TIMESTAMP) works under both ANSI modes, while to_timestamp with pattern XXX throws under Spark 4.2 default ANSI and NULLs under non-ANSI (probe in probe-notes.md), or pin the session timezone to UTC in job config.

## How to check the fix by running
WEAK ORACLE (verified): with this cutoff the flaw returns 3 rows under both session zones (see verification-log.md - the count comparison cannot separate the zones here); the defect itself is proven by pitfall 025's epoch output (1781517600 Warsaw vs 1781539200 New York for the same literal). Compare epochs, not counts, when re-designing this case.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 25 (from cases/).
