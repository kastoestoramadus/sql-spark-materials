-- PySpark job: total = spark.table('q40').agg(F.sum('id')).collect()[0][0]
SELECT sum(id) FROM q40;
