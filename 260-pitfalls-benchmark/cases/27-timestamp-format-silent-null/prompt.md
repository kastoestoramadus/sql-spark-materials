# Case 27: timestamp-format-silent-null (difficulty: easy)

After a source format change from ISO to dd/MM/yyyy, the event filter quietly matches nothing.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q27 AS SELECT * FROM VALUES ('15/01/2026 12:00') AS t(ts);
```

## Statistics
q27: 1 row, dd/MM/yyyy format.

## Query under review
```sql
SELECT to_timestamp(ts, 'yyyy-MM-dd HH:mm') AS parsed FROM q27;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
