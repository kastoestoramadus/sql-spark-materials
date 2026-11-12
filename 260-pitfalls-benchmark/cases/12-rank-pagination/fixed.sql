SELECT player, score FROM (SELECT player, score, DENSE_RANK() OVER (ORDER BY score DESC) AS drk FROM q12) WHERE drk <= 2;
