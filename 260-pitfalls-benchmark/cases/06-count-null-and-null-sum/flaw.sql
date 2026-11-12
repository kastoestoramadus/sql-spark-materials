SELECT dept, COUNT(bonus) AS rows_with_bonus, SUM(bonus) AS total FROM q06 GROUP BY dept ORDER BY dept;
