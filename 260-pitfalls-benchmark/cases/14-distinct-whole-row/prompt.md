# Case 14: distinct-whole-row (difficulty: easy)

An analyst deduplicates accounts with DISTINCT and is surprised to see account 1 twice.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q14 AS SELECT * FROM VALUES (1,'x'),(1,'y'),(2,'z') AS t(a,b);
```

## Statistics
q14: 3 rows; a=1 has two different b values.

## Query under review
```sql
SELECT DISTINCT a, b FROM q14 ORDER BY a, b;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
