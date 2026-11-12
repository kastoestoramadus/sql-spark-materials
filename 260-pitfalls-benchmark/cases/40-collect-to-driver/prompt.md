# Case 40: collect-to-driver (difficulty: hard)

A job collect()s 100k rows to the driver to sum one column in Python.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q40 AS SELECT id, (id % 100) AS grp, lpad(CAST(id AS STRING), 50, 'x') AS pad FROM range(100000);
```

## Statistics
q40: 100000 rows, 50-byte pad (~10 MB moved to the driver).

## Query under review
```sql
-- PySpark job: rows = spark.table('q40').collect(); total = sum(r['id'] for r in rows)
SELECT * FROM q40;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
