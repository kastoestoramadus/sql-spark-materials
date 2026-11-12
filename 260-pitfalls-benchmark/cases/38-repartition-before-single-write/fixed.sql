-- PySpark job: spark.table('q38').coalesce(1).write.mode('overwrite').parquet('out/')
SELECT count(*) FROM q38;
