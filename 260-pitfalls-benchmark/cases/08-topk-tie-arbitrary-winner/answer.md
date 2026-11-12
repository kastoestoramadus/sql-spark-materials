# Key 08 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 008): see repro/outputs/008-*.txt.

## Required findings (any one term suffices per line)
```required_findings
ties on the sort key
arbitrary winner
nondeterministic
```

## Decoys (count as false claims if reported as defects)
```non_defects
ORDER BY score DESC itself is correct
the four scores being equal is legitimate data
```

## Expected fix
Either return all tied rows (MAX + filter) or add a documented unique tie-break column to ORDER BY.

## How to check the fix by running
flaw.sql picks one player; df variants below show different winners under different partitioning; fixed.sql returns all tied players deterministically.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 08 (from cases/).
