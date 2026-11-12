"""e05 - Missing broadcast: SortMergeJoin (broadcast off) vs BroadcastHashJoin.

3M-row fact joined to a 200k-row dimension, aggregated. With broadcast OFF both
sides shuffle; with broadcast ON only the fact side shuffles. Reports time and
shuffle bytes written (event log).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import make_spark, save, timed  # noqa: E402

import pyspark.sql.functions as F  # noqa: E402

N_FACT, N_DIM = 3_000_000, 200_000

for threshold, name, label in [("-1", "e05_smj", "sort_merge"), ("10485760", "e05_broadcast", "broadcast")]:
    spark = make_spark(name, name, **{"spark.sql.autoBroadcastJoinThreshold": threshold})
    fact = (
        spark.range(N_FACT)
        .withColumn("customer_id", (F.col("id") % N_DIM).cast("int"))
        .withColumn("amount", (F.col("id") % 991).cast("double"))
        .select("id", "customer_id", "amount")
    )
    dim = spark.range(N_DIM).withColumn("customer_id", F.col("id").cast("int")).withColumn("region", (F.col("id") % 20).cast("string")).select("customer_id", "region")
    fact.join(dim.hint("broadcast") if label == "broadcast" else dim, "customer_id").groupBy("customer_id").agg(
        F.sum("amount")
    ).write.format("noop").mode("overwrite").save()  # warm-up
    t, _ = timed(
        lambda: fact.join(dim.hint("broadcast") if label == "broadcast" else dim, "customer_id")
        .groupBy("customer_id")
        .agg(F.sum("amount"))
        .write.format("noop")
        .mode("overwrite")
        .save()
    )
    save(name, {"join": label, "seconds": t})
    spark.stop()
