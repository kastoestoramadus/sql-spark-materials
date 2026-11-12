-- PySpark job: rows = spark.table('q40').collect(); total = sum(r['id'] for r in rows)
SELECT * FROM q40;
