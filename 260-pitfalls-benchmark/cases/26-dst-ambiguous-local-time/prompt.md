# Case 26: dst-ambiguous-local-time (difficulty: hard)

Two night-batch transactions stamped '02:30' during the DST fall-back are counted as one.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q26 AS SELECT * FROM VALUES ('2026-10-25 02:30:00','+02:00'),('2026-10-25 02:30:00','+01:00') AS t(ts,off);
```

## Statistics
q26: 2 rows, same local time with different offsets (EU fall-back 2026-10-25).

## Query under review
```sql
SELECT COUNT(DISTINCT to_timestamp(ts, 'yyyy-MM-dd HH:mm:ss')) AS distinct_instants FROM q26;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
