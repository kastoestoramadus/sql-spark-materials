# Case 10: window-default-frame (difficulty: hard)

A per-event running balance shows the full peer-group total on tied event numbers, breaking intraday reconciliation.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q10 AS SELECT * FROM VALUES (1,1,10),(1,2,20),(1,2,50),(1,3,5) AS t(acct,evt,amt);
```

## Statistics
q10: 4 rows, evt=2 duplicated (tie).

## Query under review
```sql
SELECT evt, amt, SUM(amt) OVER (PARTITION BY acct ORDER BY evt) AS running FROM q10 ORDER BY evt, amt;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
