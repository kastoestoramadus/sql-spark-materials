# Key 39 (HIDDEN FROM REVIEWER)

Defect (category: performance, from pitfall -): see repro/outputs/--*.txt.

## Required findings (any one term suffices per line)
```required_findings
skewed join key
join strategy not pinned
one straggler task processes the hot key
planner picks broadcast | sort-merge depending on stats and threshold
```

## Decoys (count as false claims if reported as defects)
```non_defects
the CASE WHEN generating k is fine
GROUP BY label is fine
```

## Expected fix
Pin the join strategy for a dimension that fits memory: /*+ BROADCAST(q39dim) */, or split the hot key (salt + aggregate twice); check the join type in the plan, not the wall clock on tiny data.

## How to check the fix by running
df variants: at the default 10 MB auto-broadcast threshold the unhinted plan HAPPENS to pick BroadcastHashJoin on this data (stats do not price the lpad width) - the strategy floats with data size and config; with the threshold disabled (simulating a dimension too big to broadcast) the unhinted query falls to SortMergeJoin on a 90%-skewed key while the hinted query still broadcasts. Timing on 20k local rows is noise - the mechanism is plan shape + the 90/10 split.
Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only 39 (from cases/).
