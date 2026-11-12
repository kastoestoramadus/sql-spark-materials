# Case 19: rounding-policy-mismatch (difficulty: medium)

Totals differ by one cent per few invoices between the Spark job and the bank's Java system.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q19 AS SELECT * FROM VALUES (CAST(2.5 AS DOUBLE)),(CAST(3.5 AS DOUBLE)) AS t(amt);
```

## Statistics
q19: 2 rows ending in .5.

## Query under review
```sql
SELECT SUM(ROUND(amt)) AS total FROM q19;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
