# Key 21 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 021): see repro/outputs/021-*.txt.

## Required findings (any one term suffices per line)
```required_findings
division without a zero guard
zero divisor possible per data
```

## Decoys (count as false claims if reported as defects)
```non_defects
returning NULL for the zero row is an acceptable policy once explicit
the 10/2 row is fine
```

## Expected fix
Guard the divisor: n / NULLIF(d, 0) (or try_divide) so the zero row yields a handled NULL instead of a job-killing exception (ANSI) or a silent NULL you never chose (non-ANSI).

## How to check the fix by running
flaw.sql throws DIVIDE_BY_ZERO in this session (ANSI on); the df variants show the same statement returning NULL with ANSI off; fixed.sql returns [5.0, NULL].
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 21 (from cases/).
