-- Planted SQL antipatterns (synthetic, no bank data) for sqlfluff / sqlglot probes
SELECT f.id, f.k, d.label, count(*) AS cnt
FROM fact_smallfiles f JOIN dim ON f.k = dim.k
WHERE f.id in (SELECT max(id) FROM fact_smallfiles GROUP BY k)
GROUP BY f.id, f.k, d.label
ORDER BY cnt desc;

select f.*, d.*
from fact_smallfiles f inner join dim d on f.k = d.k
where f.id between 1 and 10
