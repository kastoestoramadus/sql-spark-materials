# Case 38: repartition-before-single-write (difficulty: hard)

A job repartition(100)s 50k rows before writing Parquet for a single-file consumer.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q38 AS SELECT id, id % 20 AS k, lpad(CAST(id AS STRING), 100, 'p') AS pad FROM range(50000);
```

## Statistics
q38: 50000 rows, 100-byte pad, 20 distinct k.

## Query under review
```sql
-- PySpark job: spark.table('q38').repartition(100).write.mode('overwrite').parquet('out/')
-- consumed by a single-file loader
SELECT count(*) FROM q38;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
