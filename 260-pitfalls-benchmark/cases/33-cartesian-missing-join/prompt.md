# Case 33: cartesian-missing-join (difficulty: easy)

A report join got refactored; the job now runs minutes instead of seconds and its row count exploded.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q33a AS SELECT id, id % 7 AS grp FROM range(100);
CREATE OR REPLACE TEMP VIEW q33b AS SELECT id, CONCAT('n', CAST(id AS STRING)) AS nm FROM range(100);
```

## Statistics
q33a/q33b: 100 rows each.

## Query under review
```sql
SELECT COUNT(*) FROM q33a a, q33b b WHERE a.grp = 1;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
