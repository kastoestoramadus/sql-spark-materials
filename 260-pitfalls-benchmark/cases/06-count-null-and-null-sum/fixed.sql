SELECT dept, COUNT(*) AS rows_total, COALESCE(SUM(bonus),0.0) AS total FROM q06 GROUP BY dept ORDER BY dept;
