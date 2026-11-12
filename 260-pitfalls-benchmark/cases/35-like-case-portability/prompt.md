# Case 35: like-case-portability (difficulty: easy)

A 'starts with a' filter ported from sqlite misses 'Apple' on Spark.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q35 AS SELECT * FROM VALUES ('Apple'), ('apple'), ('apricot'), ('Banana') AS t(fruit);
```

## Statistics
q35: 4 fruits; one capital-A row.

## Query under review
```sql
SELECT fruit FROM q35 WHERE fruit LIKE 'a%';
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
