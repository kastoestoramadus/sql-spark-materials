# Case 03: join-null-keys (difficulty: medium)

Two customer extracts joined on account id silently lose the NULL-id rows.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q03a AS SELECT * FROM VALUES (1,'a'),(CAST(NULL AS INT),'b') AS t(k,v);
CREATE OR REPLACE TEMP VIEW q03b AS SELECT * FROM VALUES (1,'x'),(CAST(NULL AS INT),'y') AS t(k,w);
```

## Statistics
q03a/q03b: 2 rows each, NULL key on the second row.

## Query under review
```sql
SELECT a.v, b.w FROM q03a a JOIN q03b b ON a.k = b.k;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
