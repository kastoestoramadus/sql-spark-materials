-- set spark.sql.shuffle.partitions=8 (or size it) before this job
SELECT k, count(*), max(pad) FROM q36 GROUP BY k;
