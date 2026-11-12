# Key 32 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 032): see repro/outputs/032-*.txt.

## Required findings (any one term suffices per line)
```required_findings
user input unescaped in LIKE
% is a wildcard
ESCAPE
```

## Decoys (count as false claims if reported as defects)
```non_defects
ORDER BY nm is fine
the row '10 percent' matching a search for '10%' only literally is the point — matching it via wildcard is the bug
```

## Expected fix
Escape wildcards in user input (ESCAPE clause) or use position/contains functions with literal arguments.

## How to check the fix by running
flaw.sql matches '1000','10%','10 percent' (3 rows); fixed.sql matches only '10%'.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 32 (from cases/).
