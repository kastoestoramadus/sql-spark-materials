# Case 02: not-in-with-null (difficulty: medium)

A blocklist check that should flag account 1 and 3 flags nothing.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q02a AS SELECT * FROM VALUES (1),(2),(3) AS t(id);
CREATE OR REPLACE TEMP VIEW q02b AS SELECT * FROM VALUES (2),(CAST(NULL AS INT)) AS t(deny);
```

## Statistics
q02a: 3 rows; q02b: 2 rows including one NULL.

## Query under review
```sql
SELECT id FROM q02a WHERE id NOT IN (SELECT deny FROM q02b);
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
