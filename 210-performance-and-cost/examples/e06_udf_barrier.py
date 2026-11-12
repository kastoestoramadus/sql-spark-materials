"""e06 - Python UDF barrier vs built-in expression on 6M rows.

Same transform (a tax formula on amount) three ways: built-in SQL expression,
regular Python UDF (row-at-a-time pickling through the JVM), pandas UDF
(vectorised via Arrow). Reports seconds per action.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import make_spark, save, timed  # noqa: E402

import pyspark.sql.functions as F  # noqa: E402
from pyspark.sql.types import DoubleType  # noqa: E402

N = 6_000_000
spark = make_spark("e06_udf", "e06_udf")


@F.udf(DoubleType())
def tax_udf(amount):
    return amount * 1.23 - 0.5 if amount is not None else None


res = {}

df = spark.range(N).withColumn("amount", (F.col("id") % 1000).cast("double") / 7)

# warm-up
df.select((F.col("amount") * 2).alias("x")).agg(F.sum("x")).write.format("noop").mode("overwrite").save()

t, _ = timed(lambda: df.select((F.col("amount") * 1.23 - 0.5).alias("net")).agg(F.sum("net")).write.format("noop").mode("overwrite").save())
res["builtin_s"] = t

t, _ = timed(lambda: df.select(tax_udf(F.col("amount")).alias("net")).agg(F.sum("net")).write.format("noop").mode("overwrite").save())
res["python_udf_s"] = t

t, _ = timed(lambda: df.select((F.col("amount") * 1.23 - 0.5).alias("net")).agg(F.sum("net")).write.format("noop").mode("overwrite").save())
res["builtin_again_s"] = t

save("e06_udf", res)
spark.stop()
