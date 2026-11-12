# Key 27 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 027): see repro/outputs/027-*.txt.

## Required findings (any one term suffices per line)
```required_findings
wrong format pattern
to_timestamp returns NULL
no error raised
```

## Decoys (count as false claims if reported as defects)
```non_defects
the string itself is a valid timestamp in its real format
NULL semantics of the comparison are not the issue
```

## Expected fix
Fix the pattern and add a parse-failure audit count with try_to_timestamp (NULL failure rate on a sample). Under Spark 4 default ANSI mode a wrong pattern THROWS CANNOT_PARSE_TIMESTAMP instead of returning NULL - either way rows are lost unless the pattern is right.

## How to check the fix by running
flaw.sql: ansi=false -> NULL silently, Spark 4.2 default (ansi=true) -> CANNOT_PARSE_TIMESTAMP; fixed.sql parses the value and exposes the failure flag without throwing.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 27 (from cases/).
