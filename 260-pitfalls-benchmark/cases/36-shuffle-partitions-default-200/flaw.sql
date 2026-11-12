-- runs with the session default spark.sql.shuffle.partitions (200 on the cluster)
SELECT k, count(*), max(pad) FROM q36 GROUP BY k;
