# Case 30: case-sensitive-join (difficulty: easy)

A CRM merge joins contacts by name and matches nothing.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q30a AS SELECT * FROM VALUES ('ALICE',10),('bob',20) AS t(name,amt);
CREATE OR REPLACE TEMP VIEW q30b AS SELECT * FROM VALUES ('alice','x'),('BOB','y') AS t(name,grp);
```

## Statistics
q30a/q30b: 2 rows each, casing differs per row.

## Query under review
```sql
SELECT COUNT(*) FROM q30a a JOIN q30b b ON a.name = b.name;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
