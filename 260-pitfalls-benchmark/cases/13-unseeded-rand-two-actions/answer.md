# Key 13 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 013): see repro/outputs/013-*.txt.

## Required findings (any one term suffices per line)
```required_findings
unseeded rand()
nondeterministic filter
not reproducible across runs
```

## Decoys (count as false claims if reported as defects)
```non_defects
sampling ~50% of rows is a legitimate goal
rand(42) in fixed.sql is the correct pattern
```

## Expected fix
Seed the generator (rand(42)) so the predicate is reproducible, or persist the sample once and reuse it.

## How to check the fix by running
The first two df variants (unseeded, run twice) return different counts on the same data; the seeded pair returns the same count twice.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 13 (from cases/).
