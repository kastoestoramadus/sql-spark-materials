# Key 20 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 020): see repro/outputs/020-*.txt.

## Required findings (any one term suffices per line)
```required_findings
INT overflow unguarded
result depends on spark.sql.ansi.enabled
silent wraparound in non-ANSI mode
```

## Decoys (count as false claims if reported as defects)
```non_defects
INT for a and b is fine at current values
the 10+20 row is not the problem
```

## Expected fix
Widen to BIGINT before adding, or use try_add and handle NULL explicitly; decide the policy, do not inherit it from spark.sql.ansi.enabled.

## How to check the fix by running
flaw.sql throws ARITHMETIC_OVERFLOW under this session (ANSI on); the df variants show the same query silently WRAPPING to -2147483648 with ANSI off (Java-style int overflow, not NULL); try_add returns NULL for row 1 and 30 for row 2.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 20 (from cases/).
