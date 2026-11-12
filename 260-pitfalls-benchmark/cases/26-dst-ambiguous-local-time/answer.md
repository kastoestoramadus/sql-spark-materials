# Key 26 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 026): see repro/outputs/026-*.txt.

## Required findings (any one term suffices per line)
```required_findings
DST overlap | fall-back
local time ambiguous
offset required
```

## Decoys (count as false claims if reported as defects)
```non_defects
the two rows having the same wall-clock string is legitimate data
session timezone UTC is not the defect
```

## Expected fix
Parse with an explicit offset: CAST(concat(ts, off) AS TIMESTAMP) resolves each row to its true instant (to_timestamp with XXX does not work in this Spark build - probe-notes.md).

## How to check the fix by running
flaw.sql counts 1 instant; fixed.sql counts 2 (run under both tz variants in verification-log.md).
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 26 (from cases/).
