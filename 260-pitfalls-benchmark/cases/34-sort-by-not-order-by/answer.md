# Key 34 (HIDDEN FROM REVIEWER)

Defect (category: correctness, from pitfall 034): see repro/outputs/034-*.txt.

## Required findings (any one term suffices per line)
```required_findings
SORT BY is per-partition
DISTRIBUTE BY
not a global order
```

## Decoys (count as false claims if reported as defects)
```non_defects
partitioning by bucket before sorting is a legitimate technique
id % 4 as a key is fine
```

## Expected fix
Use ORDER BY for a global order (or collect and merge partitions explicitly).

## How to check the fix by running
verified oracle: in the flaw run the k column happens to stay monotone (partition layout luck) but the id order WITHIN equal k is arbitrary - flaw collected ids (8,20,0,4,12,16) for k=0 vs fixed (0,4,8,12,16,20); across runs/partitionings the interleaving also breaks k monotonicity (see pitfall 034 repro).
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 34 (from cases/).
