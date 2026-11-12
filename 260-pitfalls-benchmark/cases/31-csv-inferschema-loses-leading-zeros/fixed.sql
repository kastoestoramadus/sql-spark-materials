-- spark.read.option('header','true').schema('code STRING, name STRING').csv('31-csv-inferschema-loses-leading-zeros/data.csv')
SELECT code, tier FROM q31dim WHERE code IN ('001', '010');
