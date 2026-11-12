# Key 38 (HIDDEN FROM REVIEWER)

Defect (category: performance, from pitfall -): see repro/outputs/--*.txt.

## Required findings (any one term suffices per line)
```required_findings
repartition(100) adds a full shuffle before a single-file write
100 small files for one consumer
```

## Decoys (count as false claims if reported as defects)
```non_defects
repartition itself is a valid tool at other scales
50k rows is not the issue
```

## Expected fix
Use coalesce(1) (no shuffle) for a single-file sink, or size the partition count to the consumer; repartition only when an even spread is worth a full shuffle.

## How to check the fix by running
df variants: repartition(100).rdd.getNumPartitions() = 100 (a full hash shuffle); coalesce(1).rdd.getNumPartitions() = 1 with no shuffle stage.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 38 (from cases/).
