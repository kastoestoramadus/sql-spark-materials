-- PySpark job: spark.read.option('header','true').option('inferSchema','true').csv('31-csv-inferschema-loses-leading-zeros/data.csv').join(spark.table('q31dim'), 'code')
SELECT * FROM q31dim;
