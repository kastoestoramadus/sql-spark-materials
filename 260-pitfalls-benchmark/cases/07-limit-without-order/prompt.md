# Case 07: limit-without-order (difficulty: easy)

A sample of 'representative accounts' is taken with LIMIT for a manual review; every rerun reviews different accounts.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q07 AS SELECT id, id % 7 AS k FROM range(200);
```

## Statistics
q07: 200 rows.

## Query under review
```sql
SELECT id FROM q07 LIMIT 5;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
