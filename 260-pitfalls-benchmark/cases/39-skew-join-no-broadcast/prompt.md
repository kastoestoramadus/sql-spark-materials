# Case 39: skew-join-no-broadcast (difficulty: hard)

90% of a fact table sits on key 0 and joins a padded dimension with no broadcast hint.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q39 AS SELECT id, CASE WHEN id < 18000 THEN 0 ELSE id END AS k FROM range(20000);
CREATE OR REPLACE TEMP VIEW q39dim AS SELECT k, label, lpad(label, 3000000, 'z') AS pad FROM VALUES (0, 'hot'), (1, 'a'), (2, 'b'), (3, 'c'), (4, 'd') AS t(k, label);
```

## Statistics
q39: 20000 rows, 18000 on k=0; q39dim: 5 rows padded to ~3 MB each (~15 MB).

## Query under review
```sql
SELECT q39dim.label, count(*) AS n FROM q39 JOIN q39dim ON q39.k = q39dim.k GROUP BY q39dim.label;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
