# Case 20: integer-overflow-null-or-throw (difficulty: easy)

An accumulator column is INT and one row sits at the type limit; the job's fate depends on a config flag.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q20 AS SELECT * FROM VALUES (1, CAST(2147483647 AS INT), CAST(1 AS INT)), (2, CAST(10 AS INT), CAST(20 AS INT)) AS t(id, a, b);
```

## Statistics
q20: 2 rows; row 1 holds INT_MAX + 1 as two INTs.

## Query under review
```sql
SELECT id, a + b FROM q20;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
