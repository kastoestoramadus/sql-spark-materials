# Case 12: rank-pagination (difficulty: medium)

A leaderboard 'top 2' page shows 3 players and the next page starts at position 4.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q12 AS SELECT * FROM VALUES ('a',100),('b',90),('c',90),('d',80) AS t(player,score);
```

## Statistics
q12: 4 rows, score 90 duplicated.

## Query under review
```sql
SELECT player, score FROM (SELECT player, score, RANK() OVER (ORDER BY score DESC) AS rk FROM q12) WHERE rk <= 2;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
