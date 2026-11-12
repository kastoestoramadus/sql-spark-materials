# Case 22: cast-silent-null-filter (difficulty: medium)

A filter on a numeric-looking free-text column silently loses a third of the rows.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q22 AS SELECT * FROM VALUES ('12'),('abc'),(CAST(NULL AS STRING)) AS t(s);
```

## Statistics
q22: 3 rows, one non-numeric, one NULL.

## Query under review
```sql
SELECT s FROM q22 WHERE CAST(s AS INT) > 5;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
