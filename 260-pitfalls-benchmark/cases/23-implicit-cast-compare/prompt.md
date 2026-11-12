# Case 23: implicit-cast-compare (difficulty: easy)

A key-matching filter accepts '0010' and ' 10 ' but nobody knows why 'abc' records vanish.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q23 AS SELECT * FROM VALUES ('10'),('0010'),('10 '),('abc') AS t(s);
```

## Statistics
q23: 4 rows; three numeric-looking (one with leading zeros, one with spaces), one dirty.

## Query under review
```sql
SELECT s FROM q23 WHERE s = 10 ORDER BY s;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
