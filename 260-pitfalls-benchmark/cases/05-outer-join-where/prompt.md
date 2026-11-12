# Case 05: outer-join-where (difficulty: medium)

A LEFT JOIN was meant to keep accounts without a subscription, but the report shows only matching ones.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q05o AS SELECT * FROM VALUES (1,10),(2,CAST(NULL AS INT)) AS t(id,sid);
CREATE OR REPLACE TEMP VIEW q05s AS SELECT * FROM VALUES (10,'OPEN') AS t(sid,status);
```

## Statistics
q05o: 2 rows, one NULL sid; q05s: 1 row.

## Query under review
```sql
SELECT o.id, s.status FROM q05o o LEFT JOIN q05s s ON o.sid = s.sid WHERE s.status = 'OPEN';
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
