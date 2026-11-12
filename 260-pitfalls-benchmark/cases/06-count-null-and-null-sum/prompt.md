# Case 06: count-null-and-null-sum (difficulty: easy)

A KPI dashboard shows zero bonus rows and empty totals for department b.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q06 AS SELECT * FROM VALUES ('a',CAST(1.0 AS DOUBLE)),('a',CAST(NULL AS DOUBLE)),('b',CAST(NULL AS DOUBLE)) AS t(dept,bonus);
```

## Statistics
q06: 3 rows; bonus NULL rate 2/3.

## Query under review
```sql
SELECT dept, COUNT(bonus) AS rows_with_bonus, SUM(bonus) AS total FROM q06 GROUP BY dept ORDER BY dept;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
