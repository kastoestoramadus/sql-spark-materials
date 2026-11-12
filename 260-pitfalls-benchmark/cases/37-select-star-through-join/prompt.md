# Case 37: select-star-through-join (difficulty: hard)

An enrichment join selects * and carries 10 unused 180-byte columns through the shuffle; downstream reads two.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q37 AS SELECT id AS k, id % 40 AS d, lpad(CAST(id AS STRING), 180, 'x') AS payload_a, lpad(CAST(id AS STRING), 180, 'x') AS payload_b, lpad(CAST(id AS STRING), 180, 'x') AS payload_c, lpad(CAST(id AS STRING), 180, 'x') AS payload_d, lpad(CAST(id AS STRING), 180, 'x') AS payload_e, lpad(CAST(id AS STRING), 180, 'x') AS payload_f, lpad(CAST(id AS STRING), 180, 'x') AS payload_g, lpad(CAST(id AS STRING), 180, 'x') AS payload_h, lpad(CAST(id AS STRING), 180, 'x') AS payload_i, lpad(CAST(id AS STRING), 180, 'x') AS payload_j FROM range(20000);
CREATE OR REPLACE TEMP VIEW q37dim AS SELECT id AS d, concat('tier-', id) AS tier FROM range(40);
```

## Statistics
q37: 20000 rows, 2 key cols + 10 payloads of 180 chars; q37dim: 40 rows, tiny.

## Query under review
```sql
SELECT * FROM q37 JOIN q37dim USING (d);
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
