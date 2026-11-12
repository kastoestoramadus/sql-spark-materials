"""e04 - AQE post-shuffle coalescing: shuffle.partitions=200 (default) with a
small aggregation result; AQE off vs on. Measures time and task count of the
final reduce stage (event log shows e.g. 200 tasks collapsing to a handful).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import make_spark, save, timed  # noqa: E402

import pyspark.sql.functions as F  # noqa: E402

N = 4_000_000

for flag, name in [("false", "e04_aqe_off"), ("true", "e04_aqe_on")]:
    spark = make_spark(
        name, name, **{"spark.sql.shuffle.partitions": "200", "spark.sql.adaptive.enabled": flag}
    )
    df = spark.range(N).withColumn("k", F.col("id") % 20).withColumn("v", (F.col("id") % 977).cast("double"))
    df.groupBy("k").count().write.format("noop").mode("overwrite").save()  # warm-up
    t, _ = timed(lambda: df.groupBy("k").agg(F.sum("v")).write.format("noop").mode("overwrite").save())
    save(name, {"aqe": flag, "shuffle_partitions": 200, "seconds": t})
    spark.stop()
