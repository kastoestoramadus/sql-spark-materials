# Key 11 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 011): see repro/outputs/011-*.txt.

## Required findings (any one term suffices per line)
```required_findings
default frame ends at current row
LAST_VALUE returns current value
UNBOUNDED FOLLOWING
```

## Decoys (count as false claims if reported as defects)
```non_defects
FIRST_VALUE would work by accident — not the right mental model
ORDER BY evt inside the window is fine
```

## Expected fix
Add an explicit ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING frame.

## How to check the fix by running
flaw.sql last_amt = (10,20,30) i.e. the current row; fixed.sql = (30,30,30).
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 11 (from cases/).
