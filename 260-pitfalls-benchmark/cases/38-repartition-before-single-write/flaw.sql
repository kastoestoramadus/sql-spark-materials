-- PySpark job: spark.table('q38').repartition(100).write.mode('overwrite').parquet('out/')
-- consumed by a single-file loader
SELECT count(*) FROM q38;
