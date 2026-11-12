# Case 15: union-dedup-hides-duplicates (difficulty: easy)

A daily count report built with UNION reports 3 records where the source systems sent 6.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q15a AS SELECT * FROM VALUES (1),(2),(3) AS t(id);
CREATE OR REPLACE TEMP VIEW q15b AS SELECT * FROM VALUES (1),(2),(3) AS t(id);
```

## Statistics
q15a/q15b: identical 3-row feeds.

## Query under review
```sql
SELECT COUNT(*) FROM (SELECT id FROM q15a UNION SELECT id FROM q15b);
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
