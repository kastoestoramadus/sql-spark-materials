# Case 01: null-equality-filter (difficulty: easy)

A nightly reconciliation drops every row with a missing comment.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q01 AS SELECT * FROM VALUES (1,'ok'),(2,CAST(NULL AS STRING)),(3,'x') AS t(id,note);
```

## Statistics
q01: 3 rows, note NULL rate 1/3.

## Query under review
```sql
SELECT id FROM q01 WHERE note = NULL;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
