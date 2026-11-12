# Case 21: divide-by-zero-no-guard (difficulty: easy)

A rate column divides by a counter that is 0 for real rows.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q21 AS SELECT * FROM VALUES (10, 2), (10, 0) AS t(n, d);
```

## Statistics
q21: 2 rows; d=0 occurs once.

## Query under review
```sql
SELECT n / d FROM q21;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
