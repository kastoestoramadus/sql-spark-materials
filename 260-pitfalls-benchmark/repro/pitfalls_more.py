"""Pitfalls 020(reg only), 021-035: ANSI/casts, time zones, strings, ETL, portability."""
from __future__ import annotations

import sqlite3
from typing import Any

from pyspark.sql import functions as F

from common import Pitfall, run_cross, sql
from pitfalls_core import PITFALLS, _p020, reg

reg(dict(id="020", slug="integer-overflow", title="Integer overflow: NULL silently (non-ANSI), exception (ANSI), try_add (explicit)",
         category="ansi", engines="spark", fn=_p020,
         why="Non-ANSI Spark returns NULL on numeric overflow (silent loss); ANSI mode raises so the job fails loudly.",
         detect_static="Arithmetic on INT/BIGINT columns near type limits; check spark.sql.ansi.enabled.",
         detect_test="Property: non-NULL inputs must produce non-NULL output (fails non-ANSI).",
         source="https://spark.apache.org/docs/latest/sql-ansi-compliance.html"))


def _p021(c: Any) -> str:
    spark = c.spark
    lines: list[str] = []
    for ansi in (False, True):
        spark.conf.set("spark.sql.ansi.enabled", "true" if ansi else "false")
        try:
            lines.append(f"spark ansi={ansi} 1/0 -> {sql(spark, 'SELECT 1/0')}")
        except Exception as e:  # noqa: BLE001
            lines.append(f"spark ansi={ansi} 1/0 -> ERROR {str(e).splitlines()[0][:110]}")
    spark.conf.set("spark.sql.ansi.enabled", "false")
    lines.append(f"spark try_divide(1,0)  -> {sql(spark, 'SELECT try_divide(1,0)')}")
    lines.append(f"duckdb 1/0             -> {c.duck.sql('SELECT 1/0').fetchall()} (inf, not NULL!)")
    cur = c.sqlite.cursor()
    cur.execute("SELECT 1/0")
    lines.append(f"sqlite 1/0             -> {cur.fetchall()} (NULL)")
    return "\n".join(lines) + "\nSame expression, three answers (NULL / inf / NULL): division-by-zero semantics are engine policy, not math."


reg(dict(id="021", slug="division-by-zero", title="1/0: Spark NULL (non-ANSI) or exception (ANSI); DuckDB inf; sqlite NULL",
         category="ansi", engines="spark,duckdb,sqlite", fn=_p021,
         why="Division by zero is handled per engine/mode; DuckDB yields IEEE inf which propagates into averages instead of vanishing.",
         detect_static="Division where the divisor column can be 0; no NULLIF/try_divide guard.",
         detect_test="Feed divisor 0; assert policy explicitly (NULL, error, or inf) and compare engines for portability.",
         source="https://spark.apache.org/docs/latest/sql-ansi-compliance.html"))


def _p022(c: Any) -> str:
    spark = c.spark
    wrong = sql(spark, "SELECT s FROM VALUES ('12'),('abc'),(NULL) AS t(s) WHERE CAST(s AS INT) > 5")
    nc = sql(spark, "SELECT COUNT(*) FROM VALUES ('12'),('abc'),(NULL) AS t(s) WHERE CAST(s AS INT) IS NULL AND s IS NOT NULL")
    spark.conf.set("spark.sql.ansi.enabled", "true")
    try:
        ansi = sql(spark, "SELECT CAST('abc' AS INT)")
    except Exception as e:  # noqa: BLE001
        ansi = f"ERROR {str(e).splitlines()[0][:110]}"
    spark.conf.set("spark.sql.ansi.enabled", "false")
    duck = "error"
    try:
        duck = c.duck.sql("SELECT CAST('abc' AS INT)").fetchall()
    except Exception as e:  # noqa: BLE001
        duck = f"ERROR {str(e).splitlines()[0][:110]}"
    cur = c.sqlite.cursor()
    cur.execute("SELECT CAST('abc' AS INT)")
    lite = cur.fetchall()
    return (
        f"WRONG  WHERE CAST(s AS INT) > 5 -> {wrong} ('abc' and NULL vanished; no error, no warning)\n"
        f"observed silently-null casts -> {nc}\n"
        f"ansi=true CAST('abc' AS INT)   -> {ansi}\n"
        f"duckdb CAST('abc' AS INT)      -> {duck}\n"
        f"sqlite CAST('abc' AS INT)      -> {lite} (0!)\n"
        "Three engines, three answers: NULL vs error vs 0. Filter with try_cast or validate with a regex first."
    )


reg(dict(id="022", slug="cast-string-silent-null", title="CAST('abc' AS INT): Spark NULL, DuckDB error, sqlite 0 — silent row loss",
         category="ansi", engines="spark,duckdb,sqlite", fn=_p022,
         why="Non-ANSI Spark coerces unparseable strings to NULL inside predicates, so rows disappear instead of failing; engines disagree.",
         detect_static="CAST(string_col AS numeric) inside WHERE/JOIN; suggest try_cast + IS NULL audit count.",
         detect_test="Audit query: count rows where col IS NOT NULL AND try_cast(col AS INT) IS NULL must be 0 when column is expected numeric.",
         source="https://spark.apache.org/docs/latest/sql-ansi-compliance.html"))


def _p023(c: Any) -> str:
    r1 = sql(c.spark, "SELECT '10' = 10 AS eq, '10.0' = 10 AS eq2, 'abc' = 10 AS eq_null")
    r2 = sql(c.spark, "SELECT s FROM VALUES ('10'),('0010'),('10 '),('abc') AS t(s) WHERE s = 10")
    return (
        f"implicit cast string vs int comparisons: {r1} ('abc'=10 is UNKNOWN, not false)\n"
        f"WHERE s = 10 over ('10','0010','10 ','abc') -> {r2}\n"
        "Matching is defined by the cast ('0010' and '10 ' cast to 10 and match; 'abc' casts to NULL and is dropped silently)."
    )


reg(dict(id="023", slug="implicit-cast-compare", title="Comparing string column to number silently casts (and silently drops)",
         category="ansi", engines="spark", fn=_p023,
         why="Type coercion casts the string side to the numeric type; unparseable values become NULL and never match, with no error.",
         detect_static="Binary comparison/join with mismatched string vs numeric types (AST type check).",
         detect_test="For key columns, assert count(col <> CAST(col AS INT)::STRING) is 0 to detect unparseable keys.",
         source="https://spark.apache.org/docs/latest/sql-ref-ansi-compliance.html"))


def _p024(c: Any) -> str:
    return (
        f"Spark {c.spark.version} column (see outputs/000-cross-spark{c.spark.version[0]}.txt):\n"
        + run_cross(c.spark)
        + "\nRun the same list on Spark 3.5 via repro/cross_version.py (venv/py3) and diff to see mode/version deltas."
    )


reg(dict(id="024", slug="ansi-mode-3-vs-4", title="ANSI/cast/overflow behaviour differs by version and spark.sql.ansi.enabled",
         category="ansi", engines="spark3,spark4", fn=_p024,
         why="Same statement yields NULL, an error, or a value depending on version and mode; upgrades change results silently.",
         detect_static="Config audit of spark.sql.ansi.enabled; try_* vs plain functions inventory.",
         detect_test="Run the fixed cross_queries list on both versions/modes in CI and diff (this repo does exactly that).",
         source="https://spark.apache.org/docs/latest/sql-ansi-compliance.html"))


def _tz(spark: Any, tz: str, s: str) -> Any:
    old = spark.conf.get("spark.sql.session.timeZone")
    spark.conf.set("spark.sql.session.timeZone", tz)
    try:
        return sql(spark, f"SELECT unix_timestamp(to_timestamp('{s}', 'yyyy-MM-dd HH:mm:ss')) AS epoch")
    finally:
        spark.conf.set("spark.sql.session.timeZone", old)


def _p025(c: Any) -> str:
    s = "2026-06-15 12:00:00"
    waw = _tz(c.spark, "Europe/Warsaw", s)
    ny = _tz(c.spark, "America/New_York", s)
    return (
        f"same literal '{s}':\n"
        f"session tz Europe/Warsaw   -> {waw}\n"
        f"session tz America/New_York-> {ny}\n"
        "Timestamp strings have no zone; the session zone defines the instant. Cluster and laptop defaults differ -> data shifts by hours."
    )


reg(dict(id="025", slug="timezone-session-parse", title="Same timestamp string parses to different instants per session time zone",
         category="datetime", engines="spark", fn=_p025,
         why="TIMESTAMP parsing uses spark.sql.session.timeZone; a job run under a different default zone reads another instant.",
         detect_static="to_timestamp/unix_timestamp without explicit zone; check spark.sql.session.timeZone.",
         detect_test="Parse one known string under two session zones; epochs must differ by the zone offset (they do).",
         source="https://spark.apache.org/docs/latest/sql-ref-datetime-pattern.html"))


def _p026(c: Any) -> str:
    spark = c.spark
    spark.conf.set("spark.sql.session.timeZone", "Europe/Warsaw")
    try:
        gap = sql(spark, "SELECT to_timestamp('2026-03-29 02:30:00','yyyy-MM-dd HH:mm:ss') AS gap_ts, "
                         "unix_timestamp(to_timestamp('2026-03-29 02:30:00','yyyy-MM-dd HH:mm:ss')) AS gap_epoch")
        amb = sql(spark, "SELECT to_timestamp('2026-10-25 02:30:00','yyyy-MM-dd HH:mm:ss') AS amb_ts, "
                         "unix_timestamp(to_timestamp('2026-10-25 02:30:00','yyyy-MM-dd HH:mm:ss')) AS amb_epoch")
        around = sql(spark, "SELECT unix_timestamp(to_timestamp('2026-10-25 02:00:00','yyyy-MM-dd HH:mm:ss')) AS before_gap, "
                            "unix_timestamp(to_timestamp('2026-10-25 03:00:00','yyyy-MM-dd HH:mm:ss')) AS after_gap")
    finally:
        spark.conf.set("spark.sql.session.timeZone", "UTC")
    return (
        f"Europe/Warsaw 2026-03-29 02:30 does not exist (DST gap):   -> {gap}\n"
        f"Europe/Warsaw 2026-10-25 02:30 exists twice (DST overlap): -> {amb}\n"
        f"hour either side of the overlap: {around}\n"
        "Local wall times in the gap are shifted and in the overlap one instant is chosen; hourly sums gain/lose an hour."
    )


reg(dict(id="026", slug="timezone-dst-gap", title="DST gap/overlap wall-clock times are shifted or ambiguous",
         category="datetime", engines="spark", fn=_p026,
         why="Local timestamps without offset have no unique instant during DST transitions; Spark resolves gap times forward and picks one side on overlap.",
         detect_static="Timestamp literals/strings in local time around known transition dates; prefer 'yyyy-MM-dd HH:mm:ss XXX' with offset.",
         detect_test="Feed 02:30 on both EU transition dates of the year; assert epoch monotonicity per hour (violated).",
         source="https://spark.apache.org/docs/latest/sql-ref-datetime-pattern.html"))


def _p027(c: Any) -> str:
    c.spark.conf.set("spark.sql.ansi.enabled", "false")
    r = sql(c.spark, "SELECT to_timestamp('15/01/2026 12:00', 'yyyy-MM-dd HH:mm') AS wrong_pattern, "
                     "to_timestamp('15/01/2026 12:00', 'dd/MM/yyyy HH:mm') AS right_pattern, "
                     "count(*) OVER () AS n FROM VALUES (1) AS t(x)")
    ansi_note = "ansi=true: wrong pattern THROWS CANNOT_PARSE_TIMESTAMP (Spark 4.2 default); ansi=false: NULL for every row. Either way rows are lost."
    try:
        c.spark.conf.set("spark.sql.ansi.enabled", "true")
        try:
            c.spark.sql("SELECT to_timestamp('15/01/2026 12:00', 'yyyy-MM-dd HH:mm')").collect()
            ansi_note += " (probe: no throw)"
        except Exception as e:  # noqa: BLE001
            ansi_note += f" (probe: {str(e).splitlines()[0][:80]})"
    finally:
        c.spark.conf.set("spark.sql.ansi.enabled", "false")
    return (
        f"{r}\nA wrong format string yields NULL for every row (no error) in this non-ANSI session: downstream filters/joins silently drop everything.\n{ansi_note}\n"
        "Detect by testing that parse-null-rate is 0 on a sample before the real job."
    )


reg(dict(id="027", slug="timestamp-format-silent-null", title="to_timestamp with wrong pattern returns NULL for all rows",
         category="datetime", engines="spark", fn=_p027,
         why="Parse failures are NULLs, not exceptions, so a format mismatch empties the pipeline silently.",
         detect_static="Literal format vs sampled data format; regex pre-check of one value.",
         detect_test="Property: to_timestamp(col, fmt) IS NULL rate must be 0 on a known-good sample.",
         source="https://spark.apache.org/docs/latest/sql-ref-datetime-pattern.html"))


def _p028(c: Any) -> str:
    sp = sql(c.spark, "SELECT DATE'2026-01-31' + INTERVAL 1 MONTH AS plus_month, add_months(DATE'2026-01-31', 1) AS add_months")
    duck = c.duck.sql("SELECT DATE '2026-01-31' + INTERVAL 1 MONTH AS duck_month").fetchall()
    return (
        f"Spark: {sp} (day clamped to month end, silently)\n"
        f"DuckDB: {duck} (also clamps; type becomes TIMESTAMP)\n"
        "Neither engine errors: Jan 31 + 1 month is defined as Feb 28. Business rules that expect month-end or day-cap must be explicit."
    )


reg(dict(id="028", slug="date-month-end-clamp", title="Jan 31 + INTERVAL 1 MONTH clamps to Feb 28 silently",
         category="datetime", engines="spark,duckdb", fn=_p028,
         why="Month arithmetic clamps out-of-range days instead of failing or preserving the day number.",
         detect_static="add_months / INTERVAL n MONTH on day > 28 data.",
         detect_test="Dates on the 29th-31st; assert the business rule (clamped vs error vs last_day) explicitly.",
         source="https://spark.apache.org/docs/latest/api/sql/index.html?quote=add_months"))


def _p029(c: Any) -> str:
    r = sql(c.spark, "SELECT s FROM VALUES ('apple'),('Zebra'),('Ápple'),('banana') AS t(s) ORDER BY s")
    cur = c.sqlite.cursor()
    cur.execute("SELECT 'Zebra' < 'apple' AS z_lt_a")
    lite = cur.fetchall()
    duck = c.duck.sql("SELECT 'Zebra' < 'apple' AS z_lt_a, 'Ápple' < 'banana' AS u_lt_b").fetchall()
    return (
        f"Spark ORDER BY (binary UTF-8 codepoint order): {r}\n"
        f"sqlite 'Zebra' < 'apple': {lite} (1 = true; binary, same as Spark)\n"
        f"duckdb comparisons: {duck}\n"
        "Upper-case sorts before lower-case and accented letters after 'z'; users expecting locale (dictionary) order see 'wrong' sorting."
    )


reg(dict(id="029", slug="string-ordering-binary", title="String ORDER BY is binary codepoint order, not locale/collation order",
         category="strings", engines="spark,sqlite,duckdb", fn=_p029,
         why="Default collation is binary (UTF8String bytes); 'Zebra' < 'apple' and accented characters sort at the end.",
         detect_static="ORDER BY/LIKE/MIN/MAX on user-visible text without explicit collation; Spark 4 has COLLATE.",
         detect_test="Fixed multilingual sample; assert the expected locale order (fails under binary).",
         source="https://spark.apache.org/docs/latest/sql-ref-collation.html"))


def _p030(c: Any) -> str:
    c.spark.sql("DROP TABLE IF EXISTS t030a")
    c.spark.sql("DROP TABLE IF EXISTS t030b")
    c.spark.sql("CREATE TABLE t030a (name STRING, amt INT)")
    c.spark.sql("CREATE TABLE t030b (name STRING, grp STRING)")
    c.spark.sql("INSERT INTO t030a VALUES ('ALICE', 10),('bob', 20)")
    c.spark.sql("INSERT INTO t030b VALUES ('alice','x'),('BOB','y')")
    wrong = sql(c.spark, "SELECT COUNT(*) FROM t030a a JOIN t030b b ON a.name = b.name")
    right = sql(c.spark, "SELECT COUNT(*) FROM t030a a JOIN t030b b ON lower(a.name) = lower(b.name)")
    return (
        f"WRONG  join on raw name (case differs) -> {wrong} rows (all pairs dropped)\n"
        f"RIGHT  lower() both sides               -> {right} rows"
    )


reg(dict(id="030", slug="case-sensitive-join", title="Join keys differing only in case match nothing (= is case-sensitive)",
         category="strings", engines="spark", fn=_p030,
         why="String equality is byte equality; data merged from systems with different casing silently loses all matches.",
         detect_static="JOIN on free-text/name columns without lower()/initcap normalization.",
         detect_test="Sample-key overlap check: count of join keys matching case-insensitively minus exactly must be ~0 if clean.",
         source="https://spark.apache.org/docs/latest/sql-ref-collation.html"))


def _p031(c: Any) -> str:
    tmp = __import__("pathlib").Path(__file__).parent / "outputs" / "tmpcsv"
    tmp.mkdir(parents=True, exist_ok=True)
    f = tmp / "accounts.csv"
    f.write_text("acct,region\n001,X\n002,X\n010,Y\n", encoding="utf-8")
    wrong = c.spark.read.csv(str(f), header=True, inferSchema=True)
    t = wrong.select("acct", wrong.acct.cast("STRING").alias("acct_s")).collect()
    c.spark.sql("DROP TABLE IF EXISTS t031dim")
    c.spark.sql("CREATE TABLE t031dim (acct STRING, nm STRING)")
    c.spark.sql("INSERT INTO t031dim VALUES ('001','a'),('002','b'),('010','c')")
    dim = c.spark.table("t031dim")
    wrong_join = [wrong.join(dim, wrong.acct.cast("STRING") == dim.acct, "inner").count()]
    fixed = c.spark.read.schema("acct STRING, region STRING").csv(str(f), header=True)
    right_join = [fixed.join(dim, fixed.acct == dim.acct, "inner").count()]
    return (
        f"inferSchema=True reads acct as: {wrong.schema.simpleString()}; values become {[r['acct_s'] for r in t]}\n"
        f"WRONG join of inferred csv vs string dim table -> {wrong_join} matched rows (expect 3)\n"
        f"RIGHT explicit schema (acct STRING)           -> {right_join} matched rows"
    )


reg(dict(id="031", slug="csv-inferschema-leading-zeros", title="CSV inferSchema turns '001' into 1: leading zeros lost, joins fail",
         category="etl", engines="spark", fn=_p031,
         why="Type inference picks numeric for digit-only columns; codes with leading zeros are corrupted before they reach a join.",
         detect_static="read.csv(inferSchema=True) on files with code-like columns; require explicit schema.",
         detect_test="Round-trip check: count rows where csv value <> cast-to-string of parsed value on a sample.",
         source="https://spark.apache.org/docs/latest/sql-data-sources-csv.html"))


def _p032(c: Any) -> str:
    c.spark.sql("DROP TABLE IF EXISTS t032")
    c.spark.sql("CREATE TABLE t032 (nm STRING)")
    c.spark.sql("INSERT INTO t032 VALUES ('1000'),('10%'),('A100'),('10 percent')")
    wrong = sql(c.spark, "SELECT nm FROM t032 WHERE nm LIKE '%10%%' ORDER BY nm")
    right = sql(c.spark, "SELECT nm FROM t032 WHERE nm LIKE '%10/%%' ESCAPE '/' ORDER BY nm")
    return (
        f"user searches for the literal text '10%':\n"
        f"WRONG  LIKE '%%10%%' unescaped -> {wrong} (wildcard % matches any suffix)\n"
        f"RIGHT  LIKE '%%10/%%' ESCAPE '/' -> {right}"
    )


reg(dict(id="032", slug="like-pattern-injection", title="User input inside LIKE: % and _ act as wildcards",
         category="strings", engines="spark", fn=_p032,
         why="Interpolating search text into a LIKE pattern lets users match unintended rows (or all rows with a bare %).",
         detect_static="LIKE with concatenated user input and no ESCAPE clause; string-built SQL.",
         detect_test="Search for '10%' and '%': result sets must contain exactly the literal rows.",
         source="https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-like.html"))


def _p033(c: Any) -> str:
    c.spark.sql("DROP TABLE IF EXISTS t033a")
    c.spark.sql("DROP TABLE IF EXISTS t033b")
    c.spark.sql("CREATE TABLE t033a (id INT, grp INT)")
    c.spark.sql("CREATE TABLE t033b (id INT, nm STRING)")
    va = ",".join(f"({i},{i % 7})" for i in range(100))
    vb = ",".join(f"({i},'n{i}')" for i in range(100))
    c.spark.sql(f"INSERT INTO t033a VALUES {va}")
    c.spark.sql(f"INSERT INTO t033b VALUES {vb}")
    wrong = sql(c.spark, "SELECT COUNT(*) FROM t033a a, t033b b WHERE a.grp = 1")
    right = sql(c.spark, "SELECT COUNT(*) FROM t033a a JOIN t033b b ON a.id = b.id WHERE a.grp = 1")
    return (
        f"intended: join facts to dim on id, filter grp=1 (~14 rows)\n"
        f"WRONG  missing join predicate (comma join, only WHERE filter) -> {wrong[0][0]} rows (cartesian)\n"
        f"RIGHT  JOIN ON id                                             -> {right[0][0]} rows"
    )


reg(dict(id="033", slug="cartesian-missing-join", title="Missing join condition turns the query into a cartesian product",
         category="joins-cost", engines="spark", fn=_p033,
         why="A WHERE clause that only filters one side leaves the join without a predicate; output and cost multiply by both row counts.",
         detect_static="Join node without equality condition; CROSS JOIN in plan; row-count estimate >> inputs.",
         detect_test="Plan assertion: no CartesianProduct node; row-count sanity check.",
         source="https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-join.html"))


def _p034(c: Any) -> str:
    df = c.spark.range(0, 24).select((F.col("id") % 4).alias("k"), F.col("id"))
    partial = [(r["id"], r["k"]) for r in df.repartition(4).sortWithinPartitions("k").collect()][:8]
    full = [(r["id"], r["k"]) for r in df.orderBy("k").collect()][:8]
    return (
        f"WRONG  repartition(4).sortWithinPartitions('k') first 8 (id,k): {partial} (sorted only inside partitions)\n"
        f"RIGHT  orderBy('k') first 8: {full} (global order)"
    )


reg(dict(id="034", slug="sort-within-partitions", title="sortWithinPartitions is not a global ORDER BY",
         category="semantics", engines="spark", fn=_p034,
         why="Rows are sorted inside each partition; collect/limit over the result is interleaved, not globally ordered.",
         detect_static="DataFrame API sortWithinPartitions followed by collect/limit/write-single-file.",
         detect_test="Assert monotonicity of the collected sort key (fails).",
         source="https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.sortWithinPartitions.html"))


def _p035(c: Any) -> str:
    sp = sql(c.spark, "SELECT 'Apple' LIKE 'a%' AS spark_ci_like")
    duck = c.duck.sql("SELECT 'Apple' LIKE 'a%' AS duck_like").fetchall()
    cur = c.sqlite.cursor()
    cur.execute("SELECT 'Apple' LIKE 'a%'")
    lite = cur.fetchall()
    return (
        f"Spark  'Apple' LIKE 'a%' -> {sp} (case-sensitive)\n"
        f"DuckDB 'Apple' LIKE 'a%' -> {duck} (case-sensitive)\n"
        f"sqlite 'Apple' LIKE 'a%' -> {lite} (1 = TRUE: case-INsensitive for ASCII by default)\n"
        "The same search behaves differently per engine; a query ported from sqlite/MySQL matches extra rows in Spark."
    )


reg(dict(id="035", slug="like-case-sensitivity-portability", title="LIKE case sensitivity differs: sqlite insensitive, Spark/DuckDB sensitive",
         category="strings", engines="spark,duckdb,sqlite", fn=_p035,
         why="SQL standard LIKE is case-sensitive, but sqlite (and MySQL) default to insensitive ASCII matching; ports change result sets.",
         detect_static="LIKE predicates ported across engines; add lower() both sides or explicit COLLATE.",
         detect_test="Differential run of the same LIKE on both engines; result sets must match (they do not).",
         source="https://www.sqlite.org/lang_expr.html#the_like_glob_regexp_match_operators"))
