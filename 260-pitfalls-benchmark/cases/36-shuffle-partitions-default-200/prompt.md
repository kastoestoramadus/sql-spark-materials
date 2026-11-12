# Case 36: shuffle-partitions-default-200 (difficulty: hard)

A 10k-row nightly aggregation ships with the cluster default 200 shuffle partitions.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q36 AS SELECT id, id % 50 AS k, lpad(CAST(id AS STRING), 60, 'x') AS pad FROM range(10000);
```

## Statistics
q36: 10000 rows, 50 groups (~200 rows/group, ~60-byte pad).

## Query under review
```sql
-- runs with the session default spark.sql.shuffle.partitions (200 on the cluster)
SELECT k, count(*), max(pad) FROM q36 GROUP BY k;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
