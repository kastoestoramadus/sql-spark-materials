# Case 04: join-fanout-dup-keys (difficulty: medium)

A revenue total doubles after a dimension reload introduced duplicate keys.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q04f AS SELECT * FROM VALUES (1,10),(1,20),(2,5) AS t(acct,amt);
CREATE OR REPLACE TEMP VIEW q04d AS SELECT * FROM VALUES (1),(1) AS t(acct);
```

## Statistics
q04f: 3 rows; q04d: 2 rows, acct=1 duplicated.

## Query under review
```sql
SELECT SUM(f.amt) AS total FROM q04f f JOIN q04d d ON f.acct = d.acct;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
