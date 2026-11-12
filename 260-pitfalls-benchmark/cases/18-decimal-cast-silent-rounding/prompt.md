# Case 18: decimal-cast-silent-rounding (difficulty: easy)

A money column is narrowed with a CAST and cents silently change.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q18 AS SELECT * FROM VALUES (1, CAST('12.255' AS DECIMAL(10,3))), (2, CAST('0.125' AS DECIMAL(10,3))) AS t(id, amount);
```

## Statistics
q18: 2 rows, DECIMAL(10,3) amounts with a third decimal digit.

## Query under review
```sql
SELECT id, CAST(amount AS DECIMAL(5,2)) AS amount_2dp FROM q18;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
