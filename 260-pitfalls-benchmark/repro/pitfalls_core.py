"""Pitfalls 001-020: NULL semantics, joins, aggregates, nondeterminism, numerics.
All evidence comes from running the engine inside fn()."""
from __future__ import annotations

from typing import Any

from pyspark.sql import Window
from pyspark.sql import functions as F

from common import Pitfall, sql

PITFALLS: list[Pitfall] = []


def reg(p: Pitfall) -> None:
    PITFALLS.append(p)


def _p001(c: Any) -> str:
    c.spark.sql("DROP TABLE IF EXISTS t001")
    c.spark.sql("CREATE TABLE t001 (id INT, note STRING)")
    c.spark.sql("INSERT INTO t001 VALUES (1,'ok'), (2,NULL), (3,'fine')")
    wrong = sql(c.spark, "SELECT id FROM t001 WHERE note = NULL")
    wrong2 = sql(c.spark, "SELECT NULL = NULL AS eq")
    right = sql(c.spark, "SELECT id FROM t001 WHERE note IS NULL")
    return (
        f"WRONG  WHERE note = NULL            -> {wrong} (0 rows; NULL never equal)\n"
        f"WRONG  SELECT NULL = NULL           -> {wrong2} (NULL, not true)\n"
        f"RIGHT  WHERE note IS NULL           -> {right}"
    )


reg(dict(id="001", slug="null-equality", title="= NULL never matches; NULL = NULL is NULL",
         category="null-semantics", engines="spark", fn=_p001,
         why="Comparison with NULL yields UNKNOWN, filtered out by WHERE, so rows vanish silently.",
         detect_static="Pattern: /=[[:space:]]*NULL|<>[[:space:]]*NULL/ in predicates (AST: null literal inside comparison).",
         detect_test="Property test: count(col = NULL) must be 0 for every column; count IS NULL + IS NOT NULL = count(*).",
         source="https://spark.apache.org/docs/latest/sql-ref-null-semantics.html"))


def _p002(c: Any) -> str:
    c.spark.sql("DROP TABLE IF EXISTS t002a")
    c.spark.sql("DROP TABLE IF EXISTS t002b")
    c.spark.sql("CREATE TABLE t002a (id INT)")
    c.spark.sql("CREATE TABLE t002b (deny INT)")
    c.spark.sql("INSERT INTO t002a VALUES (1),(2),(3)")
    c.spark.sql("INSERT INTO t002b VALUES (2),(NULL)")
    wrong = sql(c.spark, "SELECT id FROM t002a WHERE id NOT IN (SELECT deny FROM t002b)")
    right = sql(c.spark,
                "SELECT a.id FROM t002a a LEFT ANTI JOIN (SELECT deny FROM t002b WHERE deny IS NOT NULL) b ON a.id = b.deny")
    right2 = sql(c.spark, "SELECT id FROM t002a WHERE id NOT IN (SELECT deny FROM t002b WHERE deny IS NOT NULL)")
    return (
        f"WRONG  NOT IN over subquery containing NULL -> {wrong} (0 rows)\n"
        f"RIGHT  LEFT ANTI JOIN with NULL filtered    -> {right}\n"
        f"RIGHT  NOT IN + WHERE deny IS NOT NULL      -> {right2}"
    )


reg(dict(id="002", slug="not-in-null", title="NOT IN with NULL in the subquery returns nothing",
         category="null-semantics", engines="spark", fn=_p002,
         why="x NOT IN (…,NULL) is UNKNOWN once one comparison is NULL, so every row is filtered out.",
         detect_static="NOT IN node whose subquery columns are nullable; suggest LEFT ANTI JOIN.",
         detect_test="Differential test: NOT IN vs LEFT ANTI JOIN on generated data with 0..30% NULL rate in the right side.",
         source="https://spark.apache.org/docs/latest/sql-ref-null-semantics.html"))


def _p003(c: Any) -> str:
    c.spark.sql("DROP TABLE IF EXISTS t003a")
    c.spark.sql("DROP TABLE IF EXISTS t003b")
    c.spark.sql("CREATE TABLE t003a (k INT, v STRING)")
    c.spark.sql("CREATE TABLE t003b (k INT, w STRING)")
    c.spark.sql("INSERT INTO t003a VALUES (1,'a'),(NULL,'b')")
    c.spark.sql("INSERT INTO t003b VALUES (1,'x'),(NULL,'y')")
    wrong = sql(c.spark, "SELECT a.v, b.w FROM t003a a JOIN t003b b ON a.k = b.k")
    right = sql(c.spark, "SELECT a.v, b.w FROM t003a a JOIN t003b b ON a.k <=> b.k")
    return (
        f"WRONG  equi-join ON a.k = b.k  -> {wrong} (NULL keys never match)\n"
        f"RIGHT  null-safe join a.k <=> b.k -> {right}"
    )


reg(dict(id="003", slug="join-null-keys", title="Join keys with NULLs are silently dropped (=) but kept with <=>",
         category="null-semantics", engines="spark", fn=_p003,
         why="Join equality is SQL =, which is UNKNOWN for NULL keys; rows with NULL keys disappear from inner joins.",
         detect_static="Join on nullable key without <=>; warn when null rate > 0.",
         detect_test="Feed rows with NULL keys, assert join output row count matches expectation (or IS NULL check appears in plan).",
         source="https://spark.apache.org/docs/latest/api/sql/index.html?quote=%3C%3D%3E"))


def _p004(c: Any) -> str:
    c.spark.sql("DROP TABLE IF EXISTS t004f")
    c.spark.sql("DROP TABLE IF EXISTS t004d")
    c.spark.sql("CREATE TABLE t004f (acct INT, amt INT)")
    c.spark.sql("CREATE TABLE t004d (acct INT)")
    c.spark.sql("INSERT INTO t004f VALUES (1,10),(1,20),(2,5)")
    c.spark.sql("INSERT INTO t004d VALUES (1),(1)")
    wrong = sql(c.spark, "SELECT SUM(f.amt) AS total FROM t004f f JOIN t004d d ON f.acct = d.acct")
    right = sql(c.spark, "SELECT SUM(amt) AS total FROM t004f WHERE acct IN (SELECT DISTINCT acct FROM t004d)")
    return (
        f"WRONG  join dup dimension keys, SUM -> {wrong} (double counted)\n"
        f"RIGHT  dedup keys before aggregate  -> {right}\n"
        "NOTE   duplicate keys also fan out row counts (2 x 2 = 4 rows for acct 1)."
    )


reg(dict(id="004", slug="join-fanout", title="Duplicate join keys fan out rows and inflate aggregates",
         category="joins", engines="spark", fn=_p004,
         why="SQL join is a multiset product per matching key; duplicate keys on either side multiply rows before aggregation.",
         detect_static="Check uniqueness of declared key/dimension columns; join on key with duplicate values in both inputs.",
         detect_test="Invariant: count(join output) <= count(left)*count(right) and per-key count = l*d; assert dimension key count distinct = count.",
         source="https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-join.html"))


def _p005(c: Any) -> str:
    c.spark.sql("DROP TABLE IF EXISTS t005o")
    c.spark.sql("DROP TABLE IF EXISTS t005s")
    c.spark.sql("CREATE TABLE t005o (id INT, sid INT)")
    c.spark.sql("CREATE TABLE t005s (sid INT, status STRING)")
    c.spark.sql("INSERT INTO t005o VALUES (1,10),(2,NULL)")
    c.spark.sql("INSERT INTO t005s VALUES (10,'OPEN')")
    wrong = sql(c.spark,
                "SELECT o.id, s.status FROM t005o o LEFT JOIN t005s s ON o.sid = s.sid WHERE s.status = 'OPEN'")
    right = sql(c.spark,
                "SELECT o.id, s.status FROM t005o o LEFT JOIN t005s s ON o.sid = s.sid AND s.status = 'OPEN'")
    return (
        f"WRONG  LEFT JOIN + WHERE right.col -> {wrong} (unmatched rows filtered: outer join became inner)\n"
        f"RIGHT  right-side predicate in ON  -> {right}"
    )


reg(dict(id="005", slug="outer-join-where-vs-on", title="WHERE on the right side of a LEFT JOIN kills unmatched rows",
         category="joins", engines="spark", fn=_p005,
         why="WHERE runs after the join; a null-rejecting predicate on the right table removes the NULL-extended rows.",
         detect_static="Outer join + WHERE on inner-side columns (null-rejecting predicate). Plan shows Join converted to Inner.",
         detect_test="Differential: same query with predicate in ON vs WHERE must agree; fail when WHERE drops rows.",
         source="https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-join.html"))


def _p006(c: Any) -> str:
    wrong = sql(c.spark, """
        SELECT dept,
               COUNT(bonus)              AS cnt_bad,
               COUNT(*)                  AS cnt_star,
               SUM(bonus)                AS sum_maybe_null
        FROM VALUES ('a',1.0),('a',NULL),('b',NULL) AS t(dept, bonus)
        GROUP BY dept ORDER BY dept
    """)
    right = sql(c.spark, """
        SELECT dept,
               COUNT(*) AS cnt_star,
               COALESCE(SUM(bonus), 0.0) AS sum_zero
        FROM VALUES ('a',1.0),('a',NULL),('b',NULL) AS t(dept, bonus)
        GROUP BY dept ORDER BY dept
    """)
    return (
        f"WRONG expectations: COUNT(col) skips NULLs, SUM over all-NULL group is NULL not 0\n"
        f"observed (count(col), count(*), sum): {wrong}\n"
        f"RIGHT (count(*), coalesce(sum,0)):    {right}"
    )


reg(dict(id="006", slug="count-nulls-and-null-sum", title="COUNT(col) vs COUNT(*); SUM of all-NULL is NULL",
         category="aggregation", engines="spark", fn=_p006,
         why="COUNT(col) counts non-NULL values only; SUM returns NULL when no non-NULL input exists, propagating NULL downstream.",
         detect_static="COUNT(<column>) where column is nullable and a row count was meant.",
         detect_test="Property: COUNT(col) + COUNT(*) >= COUNT(col); group with all NULLs must yield 0 after COALESCE.",
         source="https://spark.apache.org/docs/latest/sql-ref-functions-builtin.html"))


def _p007(c: Any) -> str:
    df = c.spark.range(0, 300)
    a = df.repartition(8).limit(5)
    b = df.repartition(23).limit(5)
    la = [r["id"] for r in a.collect()]
    lb = [r["id"] for r in b.collect()]
    r = sql(c.spark, "SELECT id FROM VALUES (3),(1),(2),(9),(0),(7) AS t(id) ORDER BY id LIMIT 3")
    return (
        f"WRONG  repartition(8).limit(5)  -> {la}\n"
        f"WRONG  repartition(23).limit(5) -> {lb}\n"
        f"       (different partitioning, different rows; no contract which)\n"
        f"RIGHT  ORDER BY id LIMIT 3      -> {r}"
    )


reg(dict(id="007", slug="limit-without-order", title="LIMIT without ORDER BY returns arbitrary rows",
         category="nondeterminism", engines="spark", fn=_p007,
         why="Limit takes the first rows of an arbitrary partial order (partition layout), not a stable subset.",
         detect_static="LIMIT without top-level ORDER BY (parser-level lint).",
         detect_test="Determinism test: run LIMIT query twice with different repartitioning; results must be identical (they are not).",
         source="https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-limit.html"))


def _p008(c: Any) -> str:
    c.spark.sql("DROP TABLE IF EXISTS t008")
    c.spark.sql("CREATE TABLE t008 (player STRING, score INT)")
    c.spark.sql("INSERT INTO t008 VALUES ('a',100),('b',100),('c',100),('d',100)")
    w = Window.orderBy(F.desc("score"))
    d = c.spark.table("t008")
    top1_a = [r["player"] for r in d.repartition(3).orderBy(F.desc("score")).limit(1).collect()]
    top1_b = [r["player"] for r in d.repartition(7).orderBy(F.desc("score")).limit(1).collect()]
    tied = [tuple(r) for r in d.withColumn("rk", F.rank().over(w)).collect()]
    return (
        f"WRONG  ORDER BY score LIMIT 1 with ties: repartition(3) -> {top1_a}, repartition(7) -> {top1_b}\n"
        f"       (tie on 100 for all four; the winner is arbitrary)\n"
        f"RIGHT  make tie-break explicit (rank shown): {tied}"
    )


reg(dict(id="008", slug="topk-ties-arbitrary", title="Top-K with ties on ORDER BY picks arbitrary rows",
         category="nondeterminism", engines="spark", fn=_p008,
         why="ORDER BY is not a total order when keys tie; LIMIT then keeps an implementation-dependent subset.",
         detect_static="ORDER BY columns whose distinct count < row count for the limit window (needs stats); at minimum: ORDER BY key + LIMIT.",
         detect_test="Data with duplicate sort keys; assert the LIMIT result set is invariant under repartitioning.",
         source="https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-limit.html"))


def _p009(c: Any) -> str:
    df = c.spark.createDataFrame([(1, "old"), (1, "new"), (2, "only")], "k INT, payload STRING")
    a = [tuple(r) for r in df.repartition(3).dropDuplicates(["k"]).collect()]
    b = [tuple(r) for r in df.repartition(7).dropDuplicates(["k"]).collect()]
    return (
        f"WRONG  dropDuplicates(['k']) repartition(3) -> {a}\n"
        f"       repartition(7)                         -> {b}\n"
        f"       (which duplicate survives is arbitrary; differs across partitioning)\n"
        f"RIGHT  pick deterministically, e.g. max(payload): "
        f"{[tuple(r) for r in df.groupBy('k').agg(F.max('payload').alias('payload')).collect()]}"
    )


reg(dict(id="009", slug="dropduplicates-arbitrary-row", title="dropDuplicates keeps an arbitrary row per key",
         category="nondeterminism", engines="spark", fn=_p009,
         why="Dedup has no ORDER BY concept; any of the duplicates may survive depending on partitioning.",
         detect_static="dropDuplicates/distinctOn with columns that do not determine the surviving row.",
         detect_test="Duplicate keys with differing payloads under two repartitionings; outputs must match (they do not).",
         source="https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.dropDuplicates.html"))


def _p010(c: Any) -> str:
    c.spark.sql("DROP TABLE IF EXISTS t010")
    c.spark.sql("CREATE TABLE t010 (acct INT, evt INT, amt INT)")
    c.spark.sql("INSERT INTO t010 VALUES (1,1,10),(1,2,20),(1,2,50),(1,3,5)")
    wrong = sql(c.spark, """
        SELECT evt, amt,
               SUM(amt) OVER (PARTITION BY acct ORDER BY evt) AS running
        FROM t010 ORDER BY evt, amt
    """)
    right = sql(c.spark, """
        SELECT evt, amt,
               SUM(amt) OVER (PARTITION BY acct ORDER BY evt
                              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running
        FROM t010 ORDER BY evt, amt
    """)
    return (
        f"WRONG (RANGE default; evt=2 peers share one total 80): {wrong}\n"
        f"RIGHT (ROWS frame; evt=2 first row sees 30, second 80): {right}"
    )


reg(dict(id="010", slug="window-default-frame", title="Ordered window defaults to RANGE frame: peers share the running total",
         category="windows", engines="spark", fn=_p010,
         why="ORDER BY without an explicit frame implies RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW, which includes all rows tied on the sort key, not just the current row.",
         detect_static="Window function with ORDER BY and no frame clause, used as a running aggregate.",
         detect_test="Data with duplicate sort keys: running value must equal the ordered prefix sum (fails with RANGE).",
         source="https://spark.apache.org/docs/latest/sql-ref-window-functions.html"))


def _p011(c: Any) -> str:
    c.spark.sql("DROP TABLE IF EXISTS t011")
    c.spark.sql("CREATE TABLE t011 (evt INT, amt INT)")
    c.spark.sql("INSERT INTO t011 VALUES (1,10),(2,20),(3,30)")
    wrong = sql(c.spark, "SELECT evt, LAST_VALUE(amt) OVER (ORDER BY evt) AS lv FROM t011 ORDER BY evt")
    right = sql(c.spark, """
        SELECT evt, LAST_VALUE(amt) OVER (
            ORDER BY evt ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS lv
        FROM t011 ORDER BY evt
    """)
    return (
        f"WRONG  LAST_VALUE with default frame -> {wrong} (frame ends at current row, returns current value)\n"
        f"RIGHT  explicit UNBOUNDED FOLLOWING -> {right}"
    )


reg(dict(id="011", slug="last-value-default-frame", title="LAST_VALUE with the default frame returns the current row",
         category="windows", engines="spark", fn=_p011,
         why="Default frame ends at CURRENT ROW, so LAST_VALUE sees only rows up to the current one.",
         detect_static="Parser lint: LAST_VALUE/FIRST_VALUE with ORDER BY and no explicit frame.",
         detect_test="Sorted data: LAST_VALUE over the window must equal the max(evt) row value (fails by default).",
         source="https://spark.apache.org/docs/latest/sql-ref-window-functions.html"))


def _p012(c: Any) -> str:
    res = sql(c.spark, """
        SELECT player, score,
               RANK() OVER (ORDER BY score DESC)       AS rk,
               DENSE_RANK() OVER (ORDER BY score DESC) AS drk,
               ROW_NUMBER() OVER (ORDER BY score DESC) AS rn
        FROM VALUES ('a',100),('b',90),('c',90),('d',80) AS t(player, score)
        ORDER BY score DESC
    """)
    return (
        f"RANK leaves gaps after ties (see player c/d), DENSE_RANK does not, ROW_NUMBER invents a total order:\n{res}\n"
        "Wrong pick: pagination or top-10-by-rank with RANK silently skips positions after every tie."
    )


reg(dict(id="012", slug="rank-vs-dense-rank", title="RANK gaps after ties vs DENSE_RANK; ROW_NUMBER is arbitrary on ties",
         category="windows", engines="spark", fn=_p012,
         why="RANK counts peers (gap), DENSE_RANK does not; ROW_NUMBER assigns arbitrary but unique numbers to tied rows.",
         detect_static="Ranking function choice near pagination/top-N logic; flag RANK used for offsets.",
         detect_test="Fixed tie data; assert expected (rk,drk) triples as above.",
         source="https://spark.apache.org/docs/latest/sql-ref-window-functions.html"))


def _p013(c: Any) -> str:
    df = c.spark.range(0, 20000)
    c1 = df.where(F.rand() < 0.5).count()
    c2 = df.where(F.rand() < 0.5).count()
    seeded = df.where(F.rand(seed=42) < 0.5).count()
    seeded2 = df.where(F.rand(seed=42) < 0.5).count()
    return (
        f"WRONG  rand() without seed: count run1 = {c1}, run2 = {c2} (re-evaluated per action, differs)\n"
        f"RIGHT  rand(seed=42): run1 = {seeded}, run2 = {seeded2} (stable across actions)"
    )


reg(dict(id="013", slug="rand-nondeterministic", title="Unseeded rand() re-evaluates per action; two actions disagree",
         category="nondeterminism", engines="spark", fn=_p013,
         why="Nondeterministic expressions are recomputed on every action (no seed, no cache), so filters/samples are not reproducible.",
         detect_static="rand()/random()/uuid() without seed used in filters or joins keys.",
         detect_test="Run the same action twice; counts must be equal (they are not), or seed the generator.",
         source="https://spark.apache.org/docs/latest/api/sql/index.html?quote=rand"))


def _p014(c: Any) -> str:
    wrong = sql(c.spark, "SELECT DISTINCT a, b FROM VALUES (1,'x'),(1,'y'),(2,'z') AS t(a,b) ORDER BY a, b")
    right = sql(c.spark, "SELECT a FROM VALUES (1,'x'),(1,'y'),(2,'z') AS t(a,b) GROUP BY a ORDER BY a")
    cd = sql(c.spark, "SELECT COUNT(DISTINCT a, b) AS pair, COUNT(DISTINCT a) AS one FROM VALUES (1,'x'),(1,'y'),(2,'z') AS t(a,b)")
    return (
        f"WRONG  DISTINCT applies to the whole row: SELECT DISTINCT a,b -> {wrong} (2 kept, a=1 twice)\n"
        f"RIGHT  one row per a needs GROUP BY a (or DISTINCT a):        -> {right}\n"
        f"observed count(distinct a,b) vs count(distinct a): {cd}"
    )


reg(dict(id="014", slug="distinct-vs-groupby", title="DISTINCT dedups the whole selected row, not the first column",
         category="aggregation", engines="spark", fn=_p014,
         why="SELECT DISTINCT removes duplicate row tuples; extra selected columns re-introduce values that looked deduplicated.",
         detect_static="DISTINCT with more projected columns than the intended key.",
         detect_test="Assert output count equals count(distinct intended key).",
         source="https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-distinct.html"))


def _p015(c: Any) -> str:
    wrong = sql(c.spark, "SELECT COUNT(*) FROM (SELECT id FROM VALUES (1),(2),(3) AS t(id) UNION SELECT id FROM VALUES (1),(2),(3) AS t(id))")
    right = sql(c.spark, "SELECT COUNT(*) FROM (SELECT id FROM VALUES (1),(2),(3) AS t(id) UNION ALL SELECT id FROM VALUES (1),(2),(3) AS t(id))")
    return (
        f"WRONG  UNION (implicit DISTINCT) count -> {wrong} (3; dedup you may not want, plus a full shuffle)\n"
        f"RIGHT  UNION ALL count                 -> {right} (6; set semantics explicit, cheaper)"
    )


reg(dict(id="015", slug="union-dedup", title="UNION deduplicates by default (semantics + hidden shuffle cost)",
         category="set-ops", engines="spark", fn=_p015,
         why="Bare UNION is UNION DISTINCT: correctness surprise when duplicates are meaningful and an avoidable shuffle+dedup cost.",
         detect_static="Parser lint: UNION without ALL.",
         detect_test="Row-count invariant: sum of input counts must equal output count when inputs are known disjoint.",
         source="https://spark.apache.org/docs/latest/sql-ref-syntax-qry-set-op.html"))


def _p016(c: Any) -> str:
    wrong = sql(c.spark, "SELECT v FROM VALUES (1),(1),(2) AS t(v) EXCEPT SELECT v FROM VALUES (2) AS t2(v)")
    right = sql(c.spark, "SELECT v FROM VALUES (1),(1),(2) AS t(v) EXCEPT ALL SELECT v FROM VALUES (2) AS t2(v)")
    return (
        f"WRONG  EXCEPT (set semantics) -> {wrong} (one 1; multiplicity of duplicates is lost)\n"
        f"RIGHT  EXCEPT ALL             -> {right} (two 1s; multiset semantics)"
    )


reg(dict(id="016", slug="except-set-semantics", title="EXCEPT drops duplicates of the left side (set vs multiset)",
         category="set-ops", engines="spark", fn=_p016,
         why="EXCEPT DISTINCT returns each surviving row once regardless of how often it occurred on the left.",
         detect_static="EXCEPT/MINUS/INTERSECT without ALL over tables where multiplicity matters.",
         detect_test="Differential: EXCEPT vs EXCEPT ALL on data with left-side duplicates.",
         source="https://spark.apache.org/docs/latest/sql-ref-syntax-qry-set-op.html"))


def _p017(c: Any) -> str:
    data = [(1e100,), (1.0,), (-1e100,), (1.0,)]
    sc = c.spark.sparkContext
    one = c.spark.createDataFrame(sc.parallelize(data, 1), "x DOUBLE").agg(F.sum("x")).collect()[0][0]
    two = c.spark.createDataFrame(sc.parallelize(data, 2), "x DOUBLE").agg(F.sum("x")).collect()[0][0]
    try:
        duck = c.duck.sql("SELECT sum(x) FROM (VALUES (1e100),(1.0),(-1e100),(1.0)) t(x)").fetchall()
    except Exception as e:  # noqa: BLE001
        duck = f"duckdb error: {str(e).splitlines()[0][:100]}"
    return (
        f"same four doubles, different partitioning:\n"
        f"WRONG/fragile  1 partition  sum -> {one!r}\n"
        f"WRONG/fragile  2 partitions sum -> {two!r}\n"
        f"DuckDB (own order)              -> {duck}\n"
        "No Kahan compensation; partial sums merge in partition order (double precision is not associative)."
    )


reg(dict(id="017", slug="float-sum-order", title="SUM over DOUBLE depends on partitioning (float addition is not associative)",
         category="numerics", engines="spark,duckdb", fn=_p017,
         why="Partial aggregation merges in partition order; reordering floating point additions changes the result.",
         detect_static="SUM/AVG over DOUBLE/FLOAT columns compared for exact equality, or used as join keys.",
         detect_test="Differential: same data in 1 vs N partitions must give bitwise-equal sums (it does not).",
         source="https://spark.apache.org/docs/latest/sql-ref-functions-builtin.html"))


def _p018(c: Any) -> str:
    out: list[str] = []
    try:
        res = sql(c.spark, """
            SELECT CAST(99999999999999999999999999999999999999 AS DECIMAL(38,0))
                 * CAST(10 AS DECIMAL(38,0)) AS times
        """)
        out.append(f"DECIMAL(38,0)*DECIMAL(38,0) -> {res}")
    except Exception as e:  # noqa: BLE001
        out.append(f"DECIMAL(38,0)*DECIMAL(38,0) -> ERROR {str(e).splitlines()[0][:140]}")
    silent = sql(c.spark, """
        SELECT CAST(CAST(12.25 AS DECIMAL(10,2)) AS DECIMAL(10,1)) AS scale_trunc,
               CAST(CAST(1 AS DECIMAL(5,4)) / CAST(3 AS DECIMAL(5,4)) AS DECIMAL(10,4)) AS div_trunc,
               CAST(123456789012345678.9 AS DOUBLE) AS dbl_loss
    """)
    out.append(f"silent scale/precision loss, no error: {silent}")
    return (
        "\n".join(out)
        + "\nOverflow RAISES (quoted) — my initial 'silent NULL' claim was refuted by this run; what IS silent: scale truncation on cast, division scale reduction, and DOUBLE conversion precision loss."
    )


reg(dict(id="018", slug="decimal-precision-loss", title="DECIMAL overflow raises; scale truncation and DOUBLE casts lose digits silently",
         category="numerics", engines="spark", fn=_p018,
         why="DECIMAL arithmetic overflow throws ArithmeticException (Spark 4.2, quoted), but narrowing casts and DOUBLE conversions round/lose digits with no error.",
         detect_static="CAST between DECIMAL precisions/scales and DOUBLE on money columns.",
         detect_test="Property: value round-trips through the declared type (fails for 12.25 -> DECIMAL(10,1)).",
         source="https://spark.apache.org/docs/latest/sql-ref-datatypes.html"))


def _p019(c: Any) -> str:
    res = sql(c.spark, """
        SELECT CAST(2.5 AS INT) AS cast_half_up,
               ROUND(2.5)       AS round_half_up,
               BROUND(2.5)      AS bround_half_even,
               ROUND(-2.5)      AS round_neg,
               BROUND(-2.5)     AS bround_neg
    """)
    py_round = round(2.5)
    duck = c.duck.sql("SELECT round(2.5) AS duck_round, CAST(2.5 AS INT) AS duck_cast").fetchall() if c.duck else "no duckdb"
    return (
        f"Spark: {res}\nPython round(2.5) = {py_round} (banker's rounding, HALF_EVEN by default)\nDuckDB: {duck}\n"
        "Spark ROUND casts HALF_UP while Python/Excel-adjacent tooling may round HALF_EVEN: same input, different cents."
    )


reg(dict(id="019", slug="decimal-rounding", title="HALF_UP vs HALF_EVEN rounding disagree across Spark round/bround, cast, Python",
         category="numerics", engines="spark,duckdb,python", fn=_p019,
         why="Spark ROUND and decimal CAST are HALF_UP; BROUND is HALF_EVEN; Python round is HALF_EVEN to even. Money rounding must be pinned explicitly.",
         detect_static="ROUND on money columns compared against non-Spark systems.",
         detect_test="Fixed .5 inputs across engines/functions; assert the chosen policy everywhere.",
         source="https://spark.apache.org/docs/latest/api/sql/index.html?quote=bround"))


def _p020(c: Any) -> str:
    out: list[str] = []
    spark = c.spark
    for ansi in (False, True):
        spark.conf.set("spark.sql.ansi.enabled", "true" if ansi else "false")
        for label, q in [
            ("int+1 over INT_MAX", "SELECT 2147483647 + 1"),
            ("bigint+1 over MAX", "SELECT 9223372036854775807 + 1"),
        ]:
            try:
                out.append(f"ansi={ansi} {label} -> {sql(spark, q)}")
            except Exception as e:  # noqa: BLE001
                out.append(f"ansi={ansi} {label} -> ERROR {str(e).splitlines()[0][:120]}")
        try:
            out.append(f"ansi={ansi} try_add      -> {sql(spark, 'SELECT try_add(2147483647, 1)')}")
        except Exception as e:  # noqa: BLE001
            out.append(f"ansi={ansi} try_add      -> ERROR {str(e).splitlines()[0][:120]}")
    spark.conf.set("spark.sql.ansi.enabled", "false")
    return "\n".join(out) + "\nNon-ANSI overflow yields NULL (silent data loss); ANSI raises; try_add returns NULL explicitly."
