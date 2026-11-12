# Case 31: csv-inferschema-loses-leading-zeros (difficulty: medium)

A CSV import with inferSchema=True silently turns codes '001' into 1 and the downstream join finds nothing.

## Schema and data (gen.sql)
```sql
CREATE OR REPLACE TEMP VIEW q31dim AS SELECT * FROM VALUES ('001','Gold'), ('010','Silver') AS t(code, tier);
```

## Statistics
data.csv: 3 rows, codes 001/002/010; dim: 2 tiers keyed by the string codes.

## Query under review
```sql
-- PySpark job: spark.read.option('header','true').option('inferSchema','true').csv('31-csv-inferschema-loses-leading-zeros/data.csv').join(spark.table('q31dim'), 'code')
SELECT * FROM q31dim;
```

Also see plan.txt (EXPLAIN of the query on this data).

## Your task
List every defect you can defend (correctness, performance, cost, maintainability), the mechanism, and the minimal fix. Do not invent data properties not shown above.
