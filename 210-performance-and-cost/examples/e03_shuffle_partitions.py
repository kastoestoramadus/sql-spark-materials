"""e03 - spark.sql.shuffle.partitions sizing: 4 vs 16 vs 200 vs 1000 on local[4].

Small aggregation over 4M rows; too few partitions under-uses cores, too many
gives scheduling overhead and tiny tasks. Reports time + per-stage task counts
from the event log.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import make_spark, save, timed  # noqa: E402

import pyspark.sql.functions as F  # noqa: E402

N = 4_000_000

for sp in [4, 16, 200, 1000]:
    name = f"e03_sp{sp}"
    spark = make_spark(name, name, **{"spark.sql.shuffle.partitions": str(sp), "spark.sql.adaptive.enabled": "false"})
    df = spark.range(N).withColumn("k", F.col("id") % 500000).withColumn("v", (F.col("id") % 977).cast("double"))
    # warm-up so codegen cost does not dominate the first config
    df.groupBy("k").count().write.format("noop").mode("overwrite").save()
    t, _ = timed(lambda: df.groupBy("k").agg(F.sum("v"), F.count("*")).write.format("noop").mode("overwrite").save())
    save(name, {"shuffle_partitions": sp, "seconds": t})
    spark.stop()
