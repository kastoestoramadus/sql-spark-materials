# Case 09: dropduplicates-arbitrary-survivor (difficulty: medium)

A dedup job keeps 'the latest' row per id using dropDuplicates; the result changes with row order.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q09 AS SELECT * FROM VALUES (1,'old','2026-01-01'),(1,'new','2026-02-01'),(2,'only','2026-03-01') AS t(id,payload,ts);
```

## Statistics
q09: 3 rows, ids {1,1,2}; id=1 has payloads old/new with distinct timestamps.

## Query under review
```sql
-- PySpark job: spark.table('q09').dropDuplicates(['id']).write.parquet('out')
SELECT id, payload, ts FROM q09;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
