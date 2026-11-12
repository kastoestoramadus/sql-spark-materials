# Case 28: month-arithmetic-31-days (difficulty: medium)

A 'same day next month' report built as '+31 days' lands in March for January 31.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q28 AS SELECT DATE'2026-01-31' AS d;
```

## Statistics
q28: one DATE row, 2026-01-31.

## Query under review
```sql
SELECT d + INTERVAL 31 DAYS AS next_month FROM q28;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
