# Key 37 (HIDDEN FROM REVIEWER)

Defect (category: cost, from pitfall -): see repro/outputs/--*.txt.

## Required findings (any one term suffices per line)
```required_findings
SELECT * through a shuffle join
unused wide columns carried into the join
column pruning defeated
```

## Decoys (count as false claims if reported as defects)
```non_defects
the join on d is correct
USING/ON style is a style choice, not the defect
```

## Expected fix
Project the columns downstream needs before the join (q37.k, q37dim.tier) so the scan prunes and the shuffle carries ~4% of the bytes.

## How to check the fix by running
df variants: the executed plan of the flaw mentions payload_* columns (>0 lines); the fixed plan mentions none (0). Shuffle cost ~20000 x 10 x 180B = 36 MB vs <1 MB.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 37 (from cases/).
