# Key 18 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 018): see repro/outputs/018-*.txt.

## Required findings (any one term suffices per line)
```required_findings
narrowing DECIMAL cast rounds silently
precision loss on money
HALF_UP applied without a policy
```

## Decoys (count as false claims if reported as defects)
```non_defects
DECIMAL(5,2) is a valid type for presentation when agreed
the values themselves are clean
```

## Expected fix
Carry the source precision (DECIMAL(10,3)) through the pipeline and round only at the final presentation step with an explicit, agreed rounding policy.

## How to check the fix by running
flaw.sql returns 12.26 and 0.13; fixed.sql returns 12.255 and 0.125 - the flaw changes the stored cents with no warning (see repro/outputs/018-*).
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 18 (from cases/).
