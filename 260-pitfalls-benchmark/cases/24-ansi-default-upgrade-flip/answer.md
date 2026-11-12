# Key 24 (HIDDEN FROM REVIEWER)

Defect (category: maintainability, from pitfall 024): see repro/outputs/024-*.txt.

## Required findings (any one term suffices per line)
```required_findings
behavior differs between Spark 3 and Spark 4 for the same query
ANSI default flipped in Spark 4
unguarded cast on dirty codes
spark.sql.ansi.enabled decides between NULL and exception
```

## Decoys (count as false claims if reported as defects)
```non_defects
pure-digit codes cast fine
try_cast returning NULL for '12x' is the intended policy
```

## Expected fix
Audit casts and arithmetic against ANSI semantics before upgrading: use try_cast/try_add/NULLIF so behaviour is pinned by the query, not by spark.sql.ansi.enabled (see repro/outputs/000-cross-spark3.txt vs 000-cross-spark4.txt and 024-ansi-mode-3-vs-4.txt).

## How to check the fix by running
flaw.sql throws in this Spark 4.2 session; the df variants show it returning NULL silently with ANSI off (the Spark 3.5 default - 000-cross-spark3.txt); try_cast returns [12, 7, NULL, NULL] under both modes.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 24 (from cases/).
