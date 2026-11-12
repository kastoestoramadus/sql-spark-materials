# Case 17: float-sum-not-associative (difficulty: hard)

Two environments compute different totals for the same reconciliation file; finance asks which one is right.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q17 AS SELECT * FROM VALUES (CAST(1e16 AS DOUBLE)),(CAST(1.0 AS DOUBLE)),(CAST(-1e16 AS DOUBLE)),(CAST(1.0 AS DOUBLE)) AS t(x);
```

## Statistics
q17: 4 DOUBLE rows mixing 1e16 and 1.0.

## Query under review
```sql
SELECT SUM(x) AS total FROM q17;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
