# Case 08: topk-tie-arbitrary-winner (difficulty: medium)

The 'top scorer' badge is awarded to a different player on every rerun of the leaderboard job.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q08 AS SELECT * FROM VALUES ('a',100),('b',100),('c',100),('d',100) AS t(player,score);
```

## Statistics
q08: 4 rows, all scores equal (tie).

## Query under review
```sql
SELECT player FROM q08 ORDER BY score DESC LIMIT 1;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
