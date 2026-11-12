# Case 24: ansi-default-upgrade-flip (difficulty: hard)

A dirty-code CAST job ran for years on Spark 3; after the Spark 4 upgrade the same jar dies at runtime.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q24 AS SELECT * FROM VALUES ('12'), ('7'), ('12x'), (CAST(NULL AS STRING)) AS t(code);
```

## Statistics
q24: 4 codes, one non-numeric ('12x'), one NULL.

## Query under review
```sql
SELECT CAST(code AS INT) FROM q24;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
