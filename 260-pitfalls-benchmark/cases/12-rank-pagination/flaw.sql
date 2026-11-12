SELECT player, score FROM (SELECT player, score, RANK() OVER (ORDER BY score DESC) AS rk FROM q12) WHERE rk <= 2;
