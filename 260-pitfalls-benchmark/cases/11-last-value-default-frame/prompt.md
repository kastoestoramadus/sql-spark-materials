# Case 11: last-value-default-frame (difficulty: medium)

An 'amount at latest event' column always equals the current row's amount.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q11 AS SELECT * FROM VALUES (1,10),(2,20),(3,30) AS t(evt,amt);
```

## Statistics
q11: 3 rows, strictly increasing evt.

## Query under review
```sql
SELECT evt, amt, LAST_VALUE(amt) OVER (ORDER BY evt) AS last_amt FROM q11 ORDER BY evt;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
