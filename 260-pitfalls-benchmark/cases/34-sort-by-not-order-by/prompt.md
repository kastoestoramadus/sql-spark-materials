# Case 34: sort-by-not-order-by (difficulty: medium)

A 'first N by key' extraction built with SORT BY returns interleaved rows.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q34 AS SELECT id, id % 4 AS k, id % 3 AS bucket FROM range(24);
```

## Statistics
q34: 24 rows, k in 0..3, bucket = id % 3.

## Query under review
```sql
SELECT id, k FROM q34 DISTRIBUTE BY bucket SORT BY k;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
