-- PySpark job: spark.table('q09').dropDuplicates(['id']).write.parquet('out')
SELECT id, payload, ts FROM q09;
