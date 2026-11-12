# Case 29: binary-string-order (difficulty: medium)

The 'first account alphabetically' badge goes to 'Zebra' although 'apple' exists.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q29 AS SELECT * FROM VALUES ('apple'),('Zebra'),('Ápple') AS t(nm);
```

## Statistics
q29: 3 rows with mixed case and one accented name.

## Query under review
```sql
SELECT nm FROM q29 ORDER BY nm LIMIT 1;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
