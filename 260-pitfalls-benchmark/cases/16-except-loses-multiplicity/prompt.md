# Case 16: except-loses-multiplicity (difficulty: medium)

A compensation job removes refunded items with EXCEPT; duplicated payments silently disappear from the result.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q16l AS SELECT * FROM VALUES (1),(1),(2) AS t(v);
CREATE OR REPLACE TEMP VIEW q16r AS SELECT * FROM VALUES (2) AS t(v);
```

## Statistics
q16l: 3 rows with v=1 twice; q16r: 1 row.

## Query under review
```sql
SELECT v FROM q16l EXCEPT SELECT v FROM q16r;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
