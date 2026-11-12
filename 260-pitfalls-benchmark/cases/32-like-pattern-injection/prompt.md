# Case 32: like-pattern-injection (difficulty: easy)

A search box for a literal reference containing % returns far too many rows.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q32 AS SELECT * FROM VALUES ('1000'),('10%'),('A100'),('10 percent') AS t(nm);
```

## Statistics
q32: 4 rows, one containing a literal percent sign.

## Query under review
```sql
SELECT nm FROM q32 WHERE nm LIKE '%10%%' ORDER BY nm;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
