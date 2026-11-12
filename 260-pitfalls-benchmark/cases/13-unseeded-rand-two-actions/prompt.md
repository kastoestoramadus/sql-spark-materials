# Case 13: unseeded-rand-two-actions (difficulty: easy)

A sampling filter uses rand() and 'the same' job reports different row counts on every rerun.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q13 AS SELECT id, id % 10 AS grp FROM range(2000);
```

## Statistics
q13: 2000 rows, 10 groups; expected sample ~1000 rows (std ~22).

## Query under review
```sql
SELECT count(*) FROM q13 WHERE rand() < 0.5;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
