"""Build benchmark cases from verified pitfalls. Run: ../venv/py4/bin/python build_cases.py (from cases/)"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

C: list[dict] = []


def case(n: str, name: str, diff: str, cat: str, pitfall: str, intro: str, gen: list[str],
         flaw: str, fixed: str, defects: list[str], non_defects: list[str], fix: str,
         verify: str, stats: str, variants: list[dict] | None = None,
         dfv: list[str] | None = None, extras: dict[str, str] | None = None) -> None:
    C.append(dict(n=n, name=name, difficulty=diff, category=cat, pitfall=pitfall, intro=intro,
                  gen=gen, flaw=flaw, fixed=fixed, defects=defects, non_defects=non_defects,
                  fix=fix, verify=verify, stats=stats, variants=variants or [{"tz": "UTC"}],
                  dfv=dfv or [], extras=extras or {}))


case("01", "null-equality-filter", "easy", "correctness", "001",
     "A nightly reconciliation drops every row with a missing comment.",
     ["CREATE OR REPLACE TEMP VIEW q01 AS SELECT * FROM VALUES (1,'ok'),(2,CAST(NULL AS STRING)),(3,'x') AS t(id,note)"],
     "SELECT id FROM q01 WHERE note = NULL",
     "SELECT id FROM q01 WHERE note IS NULL",
     ["note = NULL", "NULL comparison", "UNKNOWN"],
     ["rows with id 1 and 3 are correctly excluded", "IS NOT NULL"],
     "Replace = NULL with IS NULL (= NULL is never TRUE).",
     "flaw.sql returns 0 rows; fixed.sql returns [(2,)].",
     "q01: 3 rows, note NULL rate 1/3.")

case("02", "not-in-with-null", "medium", "correctness", "002",
     "A blocklist check that should flag account 1 and 3 flags nothing.",
     ["CREATE OR REPLACE TEMP VIEW q02a AS SELECT * FROM VALUES (1),(2),(3) AS t(id)",
      "CREATE OR REPLACE TEMP VIEW q02b AS SELECT * FROM VALUES (2),(CAST(NULL AS INT)) AS t(deny)"],
     "SELECT id FROM q02a WHERE id NOT IN (SELECT deny FROM q02b)",
     "SELECT id FROM q02a WHERE id NOT IN (SELECT deny FROM q02b WHERE deny IS NOT NULL)",
     ["NOT IN", "NULL in subquery", "no rows returned"],
     ["the deny value 2 correctly removes id 2", "IN (without NOT) would behave differently"],
     "Filter NULLs out of the subquery or use LEFT ANTI JOIN.",
     "flaw.sql returns 0 rows; fixed.sql returns [(1,),(3,)].",
     "q02a: 3 rows; q02b: 2 rows including one NULL.")

case("03", "join-null-keys", "medium", "correctness", "003",
     "Two customer extracts joined on account id silently lose the NULL-id rows.",
     ["CREATE OR REPLACE TEMP VIEW q03a AS SELECT * FROM VALUES (1,'a'),(CAST(NULL AS INT),'b') AS t(k,v)",
      "CREATE OR REPLACE TEMP VIEW q03b AS SELECT * FROM VALUES (1,'x'),(CAST(NULL AS INT),'y') AS t(k,w)"],
     "SELECT a.v, b.w FROM q03a a JOIN q03b b ON a.k = b.k",
     "SELECT a.v, b.w FROM q03a a JOIN q03b b ON a.k <=> b.k",
     ["NULL join key", "rows dropped", "null-safe equality or <=>"],
     ["row (1,'a') matching is correct", "an INNER join itself is not the defect"],
     "Use null-safe equality <=> if NULL keys must match, or clean NULLs first by policy.",
     "flaw.sql returns 1 row; fixed.sql returns 2 rows.",
     "q03a/q03b: 2 rows each, NULL key on the second row.")

case("04", "join-fanout-dup-keys", "medium", "correctness", "004",
     "A revenue total doubles after a dimension reload introduced duplicate keys.",
     ["CREATE OR REPLACE TEMP VIEW q04f AS SELECT * FROM VALUES (1,10),(1,20),(2,5) AS t(acct,amt)",
      "CREATE OR REPLACE TEMP VIEW q04d AS SELECT * FROM VALUES (1),(1) AS t(acct)"],
     "SELECT SUM(f.amt) AS total FROM q04f f JOIN q04d d ON f.acct = d.acct",
     "SELECT SUM(amt) AS total FROM q04f WHERE acct IN (SELECT DISTINCT acct FROM q04d)",
     ["duplicate key", "fan-out", "SUM inflated or double count"],
     ["the fact table rows themselves are unique", "GROUP BY acct alone would not fix it"],
     "Deduplicate dimension keys (SELECT DISTINCT) before aggregating; add uniqueness tests on keys.",
     "flaw.sql total=60; fixed.sql total=30.",
     "q04f: 3 rows; q04d: 2 rows, acct=1 duplicated.")

case("05", "outer-join-where", "medium", "correctness", "005",
     "A LEFT JOIN was meant to keep accounts without a subscription, but the report shows only matching ones.",
     ["CREATE OR REPLACE TEMP VIEW q05o AS SELECT * FROM VALUES (1,10),(2,CAST(NULL AS INT)) AS t(id,sid)",
      "CREATE OR REPLACE TEMP VIEW q05s AS SELECT * FROM VALUES (10,'OPEN') AS t(sid,status)"],
     "SELECT o.id, s.status FROM q05o o LEFT JOIN q05s s ON o.sid = s.sid WHERE s.status = 'OPEN'",
     "SELECT o.id, s.status FROM q05o o LEFT JOIN q05s s ON o.sid = s.sid AND s.status = 'OPEN'",
     ["WHERE on right table", "outer join became inner", "unmatched rows lost"],
     ["putting the s.status filter into the ON clause is the fix, not a new bug", "the LEFT keyword itself is fine"],
     "Move right-side predicates from WHERE into the ON clause (or pre-filter the right table).",
     "flaw.sql returns 1 row (id 1); fixed.sql returns 2 rows (id 2 with NULL status).",
     "q05o: 2 rows, one NULL sid; q05s: 1 row.")

case("06", "count-null-and-null-sum", "easy", "correctness", "006",
     "A KPI dashboard shows zero bonus rows and empty totals for department b.",
     ["CREATE OR REPLACE TEMP VIEW q06 AS SELECT * FROM VALUES ('a',CAST(1.0 AS DOUBLE)),('a',CAST(NULL AS DOUBLE)),('b',CAST(NULL AS DOUBLE)) AS t(dept,bonus)"],
     "SELECT dept, COUNT(bonus) AS rows_with_bonus, SUM(bonus) AS total FROM q06 GROUP BY dept ORDER BY dept",
     "SELECT dept, COUNT(*) AS rows_total, COALESCE(SUM(bonus),0.0) AS total FROM q06 GROUP BY dept ORDER BY dept",
     ["COUNT(col) skips NULL", "SUM of all-NULL is NULL", "COALESCE"],
     ["dept 'a' having one non-NULL bonus counted is correct", "ORDER BY dept is fine"],
     "Decide explicitly: COUNT(*) for rows, COUNT(col) for non-NULL values, COALESCE(SUM(...),0) for totals.",
     "flaw.sql: b shows 0 rows_with_bonus and NULL total; fixed.sql: b shows 1 row and 0.0 total.",
     "q06: 3 rows; bonus NULL rate 2/3.")

case("07", "limit-without-order", "easy", "correctness", "007",
     "A sample of 'representative accounts' is taken with LIMIT for a manual review; every rerun reviews different accounts.",
     ["CREATE OR REPLACE TEMP VIEW q07 AS SELECT id, id % 7 AS k FROM range(200)"],
     "SELECT id FROM q07 LIMIT 5",
     "SELECT id FROM q07 ORDER BY id LIMIT 5",
     ["LIMIT without ORDER BY", "nondeterministic or arbitrary rows"],
     ["200 rows being sampled is fine", "the % 7 expression is not the defect"],
     "Add a deterministic ORDER BY (unique key) before LIMIT.",
     "flaw.sql run twice under different repartitioning returns different id sets (see verification log); fixed.sql always 0-4.",
     "q07: 200 rows.",
     dfv=["spark.table('q07').repartition(8).limit(5)",
          "spark.table('q07').repartition(23).limit(5)",
          "spark.table('q07').orderBy('id').limit(5)"])

case("10", "window-default-frame", "hard", "correctness", "010",
     "A per-event running balance shows the full peer-group total on tied event numbers, breaking intraday reconciliation.",
     ["CREATE OR REPLACE TEMP VIEW q10 AS SELECT * FROM VALUES (1,1,10),(1,2,20),(1,2,50),(1,3,5) AS t(acct,evt,amt)"],
     "SELECT evt, amt, SUM(amt) OVER (PARTITION BY acct ORDER BY evt) AS running FROM q10 ORDER BY evt, amt",
     "SELECT evt, amt, SUM(amt) OVER (PARTITION BY acct ORDER BY evt ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running FROM q10 ORDER BY evt, amt",
     ["RANGE frame", "ties or peers", "running total includes peers"],
     ["PARTITION BY acct is correct", "final ORDER BY evt, amt in the outer query is fine"],
     "Add an explicit ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW frame, or make the ORDER BY unique (evt, seq).",
     "flaw.sql: both evt=2 rows show running=80; fixed.sql: 30 then 80.",
     "q10: 4 rows, evt=2 duplicated (tie).")

case("12", "rank-pagination", "medium", "correctness", "012",
     "A leaderboard 'top 2' page shows 3 players and the next page starts at position 4.",
     ["CREATE OR REPLACE TEMP VIEW q12 AS SELECT * FROM VALUES ('a',100),('b',90),('c',90),('d',80) AS t(player,score)"],
     "SELECT player, score FROM (SELECT player, score, RANK() OVER (ORDER BY score DESC) AS rk FROM q12) WHERE rk <= 2",
     "SELECT player, score FROM (SELECT player, score, DENSE_RANK() OVER (ORDER BY score DESC) AS drk FROM q12) WHERE drk <= 2",
     ["RANK", "ties", "gap or position"],
     ["ROW_NUMBER would give exactly 2 rows but loses tie information — a policy choice, not a defect"],
     "Pick the ranking policy explicitly: DENSE_RANK for no position gaps, or ROW_NUMBER with a documented tie-break.",
     "flaw.sql returns 3 players (a,b,c); fixed.sql returns 3 players but the next page continues at 3 (no skipped position).",
     "q12: 4 rows, score 90 duplicated.")

case("14", "distinct-whole-row", "easy", "correctness", "014",
     "An analyst deduplicates accounts with DISTINCT and is surprised to see account 1 twice.",
     ["CREATE OR REPLACE TEMP VIEW q14 AS SELECT * FROM VALUES (1,'x'),(1,'y'),(2,'z') AS t(a,b)"],
     "SELECT DISTINCT a, b FROM q14 ORDER BY a, b",
     "SELECT a FROM q14 GROUP BY a ORDER BY a",
     ["DISTINCT applies to whole row", "extra column", "two rows for a=1"],
     ["(2,'z') appearing once is correct", "ORDER BY a,b is not the issue"],
     "Project only the key you deduplicate on (GROUP BY a / DISTINCT a).",
     "flaw.sql returns 3 rows; fixed.sql returns 2 rows.",
     "q14: 3 rows; a=1 has two different b values.")

case("16", "except-loses-multiplicity", "medium", "correctness", "016",
     "A compensation job removes refunded items with EXCEPT; duplicated payments silently disappear from the result.",
     ["CREATE OR REPLACE TEMP VIEW q16l AS SELECT * FROM VALUES (1),(1),(2) AS t(v)",
      "CREATE OR REPLACE TEMP VIEW q16r AS SELECT * FROM VALUES (2) AS t(v)"],
     "SELECT v FROM q16l EXCEPT SELECT v FROM q16r",
     "SELECT v FROM q16l EXCEPT ALL SELECT v FROM q16r",
     ["EXCEPT DISTINCT", "multiplicity or duplicates removed", "set semantics"],
     ["value 2 being removed is correct", "INTERSECT is not involved"],
     "Use EXCEPT ALL when duplicates are meaningful, or aggregate with counts.",
     "flaw.sql returns 1 row (one 1); fixed.sql returns 2 rows (1,1).",
     "q16l: 3 rows with v=1 twice; q16r: 1 row.")

case("17", "float-sum-not-associative", "hard", "correctness", "017",
     "Two environments compute different totals for the same reconciliation file; finance asks which one is right.",
     ["CREATE OR REPLACE TEMP VIEW q17 AS SELECT * FROM VALUES (CAST(1e16 AS DOUBLE)),(CAST(1.0 AS DOUBLE)),(CAST(-1e16 AS DOUBLE)),(CAST(1.0 AS DOUBLE)) AS t(x)"],
     "SELECT SUM(x) AS total FROM q17",
     "SELECT CAST(SUM(CAST(x AS DECIMAL(20,2))) AS DOUBLE) AS total_exact FROM q17",
     ["floating point", "order of summation or partitioning", "not associative"],
     ["DuckDB or another engine returning a different value is not a Spark bug — same non-associativity"],
     "Aggregate in DECIMAL (or integer cents) for money, or compare with a tolerance, never exact equality on DOUBLE sums.",
     "SUM over the 4 values yields 1.0 in 1 partition and 2.0 in 2 partitions (see verification log); DECIMAL fixed path is exact.",
     "q17: 4 DOUBLE rows mixing 1e16 and 1.0.",
     dfv=["spark.table('q17').repartition(1).agg(F.sum('x')).collect()[0][0]",
          "spark.table('q17').repartition(2).agg(F.sum('x')).collect()[0][0]"])

case("19", "rounding-policy-mismatch", "medium", "correctness", "019",
     "Totals differ by one cent per few invoices between the Spark job and the bank's Java system.",
     ["CREATE OR REPLACE TEMP VIEW q19 AS SELECT * FROM VALUES (CAST(2.5 AS DOUBLE)),(CAST(3.5 AS DOUBLE)) AS t(amt)"],
     "SELECT SUM(ROUND(amt)) AS total FROM q19",
     "SELECT SUM(BROUND(amt)) AS total FROM q19",
     ["HALF_UP", "HALF_EVEN or banker", "bround"],
     ["round(2.5)=3 alone is not a bug — the mismatch of policies is"],
     "Pin one rounding policy across systems: BROUND (HALF_EVEN) where the other system uses banker's rounding, and document it.",
     "flaw.sql total=7; fixed.sql total=6.",
     "q19: 2 rows ending in .5.")

case("22", "cast-silent-null-filter", "medium", "correctness", "022",
     "A filter on a numeric-looking free-text column silently loses a third of the rows.",
     ["CREATE OR REPLACE TEMP VIEW q22 AS SELECT * FROM VALUES ('12'),('abc'),(CAST(NULL AS STRING)) AS t(s)"],
     "SELECT s FROM q22 WHERE CAST(s AS INT) > 5",
     "SELECT s FROM q22 WHERE TRY_CAST(s AS INT) > 5",
     ["CAST returns NULL", "unparseable", "rows silently dropped"],
     ["the NULL row being excluded is ordinary NULL semantics, not the cast defect"],
     "Use TRY_CAST plus an explicit audit/count of parse failures; decide a policy for dirty values.",
     "flaw.sql under ansi=false returns only '12' silently (rows lost); under Spark 4 default (ansi=true) it throws CAST_INVALID_INPUT; fixed.sql (TRY_CAST) returns '12' and the dirty value is countable via TRY_CAST IS NULL AND s IS NOT NULL.",
     "q22: 3 rows, one non-numeric, one NULL.")

case("25", "timezone-session-parse", "hard", "correctness", "025",
     "An evening cutoff report counts different numbers of transactions depending on which node runs it.",
     ["CREATE OR REPLACE TEMP VIEW q25 AS SELECT * FROM VALUES ('2026-06-15 10:30:00'),('2026-06-15 12:30:00'),('2026-06-15 14:30:00') AS t(ts)",
      "CREATE OR REPLACE TEMP VIEW q25cutoff AS SELECT 1781515200L AS cutoff_epoch"],
     "SELECT COUNT(*) FROM q25 e JOIN q25cutoff c ON unix_timestamp(to_timestamp(e.ts, 'yyyy-MM-dd HH:mm:ss')) >= c.cutoff_epoch",
     "SELECT COUNT(*) FROM q25 e JOIN q25cutoff c ON unix_timestamp(CAST(concat(e.ts, '+00:00') AS TIMESTAMP)) >= c.cutoff_epoch",
     ["session time zone", "to_timestamp without zone", "epoch differs"],
     ["the cutoff being an epoch number is fine; only the parsing side is ambiguous"],
     "Parse with an explicit offset: CAST(concat(ts,'+00:00') AS TIMESTAMP) works under both ANSI modes, while to_timestamp with pattern XXX throws under Spark 4.2 default ANSI and NULLs under non-ANSI (probe in probe-notes.md), or pin the session timezone to UTC in job config.",
     "WEAK ORACLE (verified): with this cutoff the flaw returns 3 rows under both session zones (see verification-log.md - the count comparison cannot separate the zones here); the defect itself is proven by pitfall 025's epoch output (1781517600 Warsaw vs 1781539200 New York for the same literal). Compare epochs, not counts, when re-designing this case.",
     "q25: 3 rows, string timestamps without offset.",
     variants=[{"tz": "UTC"}, {"tz": "America/New_York"}])

case("30", "case-sensitive-join", "easy", "correctness", "030",
     "A CRM merge joins contacts by name and matches nothing.",
     ["CREATE OR REPLACE TEMP VIEW q30a AS SELECT * FROM VALUES ('ALICE',10),('bob',20) AS t(name,amt)",
      "CREATE OR REPLACE TEMP VIEW q30b AS SELECT * FROM VALUES ('alice','x'),('BOB','y') AS t(name,grp)"],
     "SELECT COUNT(*) FROM q30a a JOIN q30b b ON a.name = b.name",
     "SELECT COUNT(*) FROM q30a a JOIN q30b b ON lower(a.name) = lower(b.name)",
     ["case-sensitive", "join drops matches", "lower()"],
     ["the amounts and groups are irrelevant", "NULL names are not involved here"],
     "Normalize key casing (lower/initcap) on both sides before joining.",
     "flaw.sql returns 0; fixed.sql returns 2.",
     "q30a/q30b: 2 rows each, casing differs per row.")

case("33", "cartesian-missing-join", "easy", "cost", "033",
     "A report join got refactored; the job now runs minutes instead of seconds and its row count exploded.",
     ["CREATE OR REPLACE TEMP VIEW q33a AS SELECT id, id % 7 AS grp FROM range(100)",
      "CREATE OR REPLACE TEMP VIEW q33b AS SELECT id, CONCAT('n', CAST(id AS STRING)) AS nm FROM range(100)"],
     "SELECT COUNT(*) FROM q33a a, q33b b WHERE a.grp = 1",
     "SELECT COUNT(*) FROM q33a a JOIN q33b b ON a.id = b.id WHERE a.grp = 1",
     ["cartesian", "missing join condition", "row count multiplies"],
     ["filtering grp=1 first is a valid optimisation, not the defect"],
     "Add the join predicate (a.id = b.id); check the plan for CartesianProduct.",
     "flaw.sql returns 100*14=1400 rows counted; fixed.sql returns 14; plan shows CartesianProduct vs SortMergeJoin/ShuffledHashJoin.",
     "q33a/q33b: 100 rows each.")

case("08", "topk-tie-arbitrary-winner", "medium", "correctness", "008",
     "The 'top scorer' badge is awarded to a different player on every rerun of the leaderboard job.",
     ["CREATE OR REPLACE TEMP VIEW q08 AS SELECT * FROM VALUES ('a',100),('b',100),('c',100),('d',100) AS t(player,score)"],
     "SELECT player FROM q08 ORDER BY score DESC LIMIT 1",
     "SELECT collect_list(player) AS tied_top FROM q08 WHERE score = (SELECT MAX(score) FROM q08)",
     ["ties on the sort key", "arbitrary winner", "nondeterministic"],
     ["ORDER BY score DESC itself is correct", "the four scores being equal is legitimate data"],
     "Either return all tied rows (MAX + filter) or add a documented unique tie-break column to ORDER BY.",
     "flaw.sql picks one player; df variants below show different winners under different partitioning; fixed.sql returns all tied players deterministically.",
     "q08: 4 rows, all scores equal (tie).",
     dfv=["spark.table('q08').repartition(3).orderBy('score', ascending=False).limit(1).collect()[0][0]",
          "spark.table('q08').repartition(7).orderBy('score', ascending=False).limit(1).collect()[0][0]"])

case("11", "last-value-default-frame", "medium", "correctness", "011",
     "An 'amount at latest event' column always equals the current row's amount.",
     ["CREATE OR REPLACE TEMP VIEW q11 AS SELECT * FROM VALUES (1,10),(2,20),(3,30) AS t(evt,amt)"],
     "SELECT evt, amt, LAST_VALUE(amt) OVER (ORDER BY evt) AS last_amt FROM q11 ORDER BY evt",
     "SELECT evt, amt, LAST_VALUE(amt) OVER (ORDER BY evt ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS last_amt FROM q11 ORDER BY evt",
     ["default frame ends at current row", "LAST_VALUE returns current value", "UNBOUNDED FOLLOWING"],
     ["FIRST_VALUE would work by accident — not the right mental model", "ORDER BY evt inside the window is fine"],
     "Add an explicit ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING frame.",
     "flaw.sql last_amt = (10,20,30) i.e. the current row; fixed.sql = (30,30,30).",
     "q11: 3 rows, strictly increasing evt.")

case("15", "union-dedup-hides-duplicates", "easy", "correctness", "015",
     "A daily count report built with UNION reports 3 records where the source systems sent 6.",
     ["CREATE OR REPLACE TEMP VIEW q15a AS SELECT * FROM VALUES (1),(2),(3) AS t(id)",
      "CREATE OR REPLACE TEMP VIEW q15b AS SELECT * FROM VALUES (1),(2),(3) AS t(id)"],
     "SELECT COUNT(*) FROM (SELECT id FROM q15a UNION SELECT id FROM q15b)",
     "SELECT COUNT(*) FROM (SELECT id FROM q15a UNION ALL SELECT id FROM q15b)",
     ["UNION without ALL", "implicit DISTINCT", "duplicates removed"],
     ["the individual id values are correct", "UNION ALL being cheaper is a bonus, not the defect"],
     "Use UNION ALL when duplicates are meaningful (or dedupe deliberately at one place).",
     "flaw.sql counts 3; fixed.sql counts 6.",
     "q15a/q15b: identical 3-row feeds.")

case("27", "timestamp-format-silent-null", "easy", "correctness", "027",
     "After a source format change from ISO to dd/MM/yyyy, the event filter quietly matches nothing.",
     ["CREATE OR REPLACE TEMP VIEW q27 AS SELECT * FROM VALUES ('15/01/2026 12:00') AS t(ts)"],
     "SELECT to_timestamp(ts, 'yyyy-MM-dd HH:mm') AS parsed FROM q27",
     "SELECT to_timestamp(ts, 'dd/MM/yyyy HH:mm') AS parsed, try_to_timestamp(ts, 'yyyy-MM-dd HH:mm') IS NULL AS parse_failed FROM q27",
     ["wrong format pattern", "to_timestamp returns NULL", "no error raised"],
     ["the string itself is a valid timestamp in its real format", "NULL semantics of the comparison are not the issue"],
     "Fix the pattern and add a parse-failure audit count with try_to_timestamp (NULL failure rate on a sample). Under Spark 4 default ANSI mode a wrong pattern THROWS CANNOT_PARSE_TIMESTAMP instead of returning NULL - either way rows are lost unless the pattern is right.",
     "flaw.sql: ansi=false -> NULL silently, Spark 4.2 default (ansi=true) -> CANNOT_PARSE_TIMESTAMP; fixed.sql parses the value and exposes the failure flag without throwing.",
     "q27: 1 row, dd/MM/yyyy format.")

case("28", "month-arithmetic-31-days", "medium", "correctness", "028",
     "A 'same day next month' report built as '+31 days' lands in March for January 31.",
     ["CREATE OR REPLACE TEMP VIEW q28 AS SELECT DATE'2026-01-31' AS d"],
     "SELECT d + INTERVAL 31 DAYS AS next_month FROM q28",
     "SELECT d + INTERVAL 1 MONTH AS next_month FROM q28",
     ["fixed 31-day month assumption", "skips February", "INTERVAL 1 MONTH clamps"],
     ["the date literal being end-of-month is not itself a defect", "datediff is not used here"],
     "Use INTERVAL 1 MONTH (clamps to month end) or an explicit business rule for day>=29.",
     "flaw.sql returns 2026-03-03; fixed.sql returns 2026-02-28.",
     "q28: one DATE row, 2026-01-31.")

case("29", "binary-string-order", "medium", "correctness", "029",
     "The 'first account alphabetically' badge goes to 'Zebra' although 'apple' exists.",
     ["CREATE OR REPLACE TEMP VIEW q29 AS SELECT * FROM VALUES ('apple'),('Zebra'),('Ápple') AS t(nm)"],
     "SELECT nm FROM q29 ORDER BY nm LIMIT 1",
     "SELECT nm FROM q29 ORDER BY nm COLLATE UNICODE_CI LIMIT 1",
     ["binary or codepoint ordering", "uppercase sorts first", "collation"],
     ["the three names are all valid data", "LIMIT 1 here is legitimate because ORDER BY is total under a collation"],
     "Use an explicit COLLATE (Spark 4 collation) or a normalised sort-key column; document that default order is binary.",
     "flaw.sql returns 'Zebra'; fixed.sql returns 'apple' under case-insensitive Unicode collation.",
     "q29: 3 rows with mixed case and one accented name.")

case("32", "like-pattern-injection", "easy", "correctness", "032",
     "A search box for a literal reference containing % returns far too many rows.",
     ["CREATE OR REPLACE TEMP VIEW q32 AS SELECT * FROM VALUES ('1000'),('10%'),('A100'),('10 percent') AS t(nm)"],
     "SELECT nm FROM q32 WHERE nm LIKE '%10%%' ORDER BY nm",
     "SELECT nm FROM q32 WHERE nm LIKE '%10/%%' ESCAPE '/' ORDER BY nm",
     ["user input unescaped in LIKE", "% is a wildcard", "ESCAPE"],
     ["ORDER BY nm is fine", "the row '10 percent' matching a search for '10%' only literally is the point — matching it via wildcard is the bug"],
     "Escape wildcards in user input (ESCAPE clause) or use position/contains functions with literal arguments.",
     "flaw.sql matches '1000','10%','10 percent' (3 rows); fixed.sql matches only '10%'.",
     "q32: 4 rows, one containing a literal percent sign.")


case("23", "implicit-cast-compare", "easy", "correctness", "023",
     "A key-matching filter accepts '0010' and ' 10 ' but nobody knows why 'abc' records vanish.",
     ["CREATE OR REPLACE TEMP VIEW q23 AS SELECT * FROM VALUES ('10'),('0010'),('10 '),('abc') AS t(s)"],
     "SELECT s FROM q23 WHERE s = 10 ORDER BY s",
     "SELECT s, TRY_CAST(s AS INT) AS k FROM q23 ORDER BY s",
     ["implicit cast of string to int", "unparseable becomes NULL", "silent row loss"],
     ["'0010' matching 10 is correct cast behaviour, not a bug", "the ORDER BY is irrelevant"],
     "Compare with an explicit TRY_CAST (and audit NULL casts), or cast the literal to string when the key is a string.",
     "flaw.sql: ansi=false -> (' 10 ','0010','10') with 'abc' silently dropped; Spark 4.2 default (ansi=true) -> CAST_INVALID_INPUT error; fixed.sql shows every value with its cast key.",
     "q23: 4 rows; three numeric-looking (one with leading zeros, one with spaces), one dirty.")

case("26", "dst-ambiguous-local-time", "hard", "correctness", "026",
     "Two night-batch transactions stamped '02:30' during the DST fall-back are counted as one.",
     ["CREATE OR REPLACE TEMP VIEW q26 AS SELECT * FROM VALUES ('2026-10-25 02:30:00','+02:00'),('2026-10-25 02:30:00','+01:00') AS t(ts,off)"],
     "SELECT COUNT(DISTINCT to_timestamp(ts, 'yyyy-MM-dd HH:mm:ss')) AS distinct_instants FROM q26",
     "SELECT COUNT(DISTINCT CAST(concat(ts, off) AS TIMESTAMP)) AS distinct_instants FROM q26",
     ["DST overlap or fall-back", "local time ambiguous", "offset required"],
     ["the two rows having the same wall-clock string is legitimate data", "session timezone UTC is not the defect"],
     "Parse with an explicit offset: CAST(concat(ts, off) AS TIMESTAMP) resolves each row to its true instant (to_timestamp with XXX does not work in this Spark build - probe-notes.md).",
     "flaw.sql counts 1 instant; fixed.sql counts 2 (run under both tz variants in verification-log.md).",
     "q26: 2 rows, same local time with different offsets (EU fall-back 2026-10-25).",
     variants=[{"tz": "UTC"}, {"tz": "Europe/Warsaw"}])

case("34", "sort-by-not-order-by", "medium", "correctness", "034",
     "A 'first N by key' extraction built with SORT BY returns interleaved rows.",
     ["CREATE OR REPLACE TEMP VIEW q34 AS SELECT id, id % 4 AS k, id % 3 AS bucket FROM range(24)"],
     "SELECT id, k FROM q34 DISTRIBUTE BY bucket SORT BY k",
     "SELECT id, k FROM q34 ORDER BY k, id",
     ["SORT BY is per-partition", "DISTRIBUTE BY", "not a global order"],
     ["partitioning by bucket before sorting is a legitimate technique", "id % 4 as a key is fine"],
     "Use ORDER BY for a global order (or collect and merge partitions explicitly).",
     "verified oracle: in the flaw run the k column happens to stay monotone (partition layout luck) but the id order WITHIN equal k is arbitrary - flaw collected ids (8,20,0,4,12,16) for k=0 vs fixed (0,4,8,12,16,20); across runs/partitionings the interleaving also breaks k monotonicity (see pitfall 034 repro).",
     "q34: 24 rows, k in 0..3, bucket = id % 3.")


case("09", "dropduplicates-arbitrary-survivor", "medium", "correctness", "009",
     "A dedup job keeps 'the latest' row per id using dropDuplicates; the result changes with row order.",
     ["CREATE OR REPLACE TEMP VIEW q09 AS SELECT * FROM VALUES (1,'old','2026-01-01'),(1,'new','2026-02-01'),"
      "(2,'only','2026-03-01') AS t(id,payload,ts)"],
     "-- PySpark job: spark.table('q09').dropDuplicates(['id']).write.parquet('out')\n"
     "SELECT id, payload, ts FROM q09",
     "SELECT id, payload, ts FROM (SELECT id, payload, ts, row_number() OVER "
     "(PARTITION BY id ORDER BY ts DESC) rn FROM q09) WHERE rn = 1",
     ["dropDuplicates keeps an arbitrary row", "which duplicate survives is not defined", "no ordering rule"],
     ["keeping one row per id is the goal itself", "repartition(1) in the variants only exposes the order dependence"],
     "State the winner explicitly: row_number() OVER (PARTITION BY id ORDER BY ts DESC) = 1, or max_by/argmax aggregation.",
     "The two df variants sort the same data differently before dropDuplicates and get different payloads "
     "for id=1 ('old' vs 'new'); fixed.sql always returns 'new' (latest ts).",
     "q09: 3 rows, ids {1,1,2}; id=1 has payloads old/new with distinct timestamps.",
     dfv=["spark.table('q09').repartition(1).sortWithinPartitions('ts').dropDuplicates(['id']).orderBy('id').collect()",
          "spark.table('q09').repartition(1).sortWithinPartitions(F.desc('ts')).dropDuplicates(['id']).orderBy('id').collect()"])

case("13", "unseeded-rand-two-actions", "easy", "correctness", "013",
     "A sampling filter uses rand() and 'the same' job reports different row counts on every rerun.",
     ["CREATE OR REPLACE TEMP VIEW q13 AS SELECT id, id % 10 AS grp FROM range(2000)"],
     "SELECT count(*) FROM q13 WHERE rand() < 0.5",
     "SELECT count(*) FROM q13 WHERE rand(42) < 0.5",
     ["unseeded rand()", "nondeterministic filter", "not reproducible across runs"],
     ["sampling ~50% of rows is a legitimate goal", "rand(42) in fixed.sql is the correct pattern"],
     "Seed the generator (rand(42)) so the predicate is reproducible, or persist the sample once and reuse it.",
     "The first two df variants (unseeded, run twice) return different counts on the same data; the seeded "
     "pair returns the same count twice.",
     "q13: 2000 rows, 10 groups; expected sample ~1000 rows (std ~22).",
     dfv=["spark.sql('SELECT count(*) FROM q13 WHERE rand() < 0.5').collect()",
          "spark.sql('SELECT count(*) FROM q13 WHERE rand() < 0.5').collect()",
          "spark.sql('SELECT count(*) FROM q13 WHERE rand(42) < 0.5').collect()",
          "spark.sql('SELECT count(*) FROM q13 WHERE rand(42) < 0.5').collect()"])

case("18", "decimal-cast-silent-rounding", "easy", "correctness", "018",
     "A money column is narrowed with a CAST and cents silently change.",
     ["CREATE OR REPLACE TEMP VIEW q18 AS SELECT * FROM VALUES (1, CAST('12.255' AS DECIMAL(10,3))), "
      "(2, CAST('0.125' AS DECIMAL(10,3))) AS t(id, amount)"],
     "SELECT id, CAST(amount AS DECIMAL(5,2)) AS amount_2dp FROM q18",
     "SELECT id, CAST(amount AS DECIMAL(10,3)) AS amount_exact FROM q18",
     ["narrowing DECIMAL cast rounds silently", "precision loss on money", "HALF_UP applied without a policy"],
     ["DECIMAL(5,2) is a valid type for presentation when agreed", "the values themselves are clean"],
     "Carry the source precision (DECIMAL(10,3)) through the pipeline and round only at the final "
     "presentation step with an explicit, agreed rounding policy.",
     "flaw.sql returns 12.26 and 0.13; fixed.sql returns 12.255 and 0.125 - the flaw changes the "
     "stored cents with no warning (see repro/outputs/018-*).",
     "q18: 2 rows, DECIMAL(10,3) amounts with a third decimal digit.")

case("20", "integer-overflow-null-or-throw", "easy", "correctness", "020",
     "An accumulator column is INT and one row sits at the type limit; the job's fate depends on a config flag.",
     ["CREATE OR REPLACE TEMP VIEW q20 AS SELECT * FROM VALUES (1, CAST(2147483647 AS INT), CAST(1 AS INT)), "
      "(2, CAST(10 AS INT), CAST(20 AS INT)) AS t(id, a, b)"],
     "SELECT id, a + b FROM q20",
     "SELECT id, try_add(a, b) FROM q20",
     ["INT overflow unguarded", "result depends on spark.sql.ansi.enabled",
      "silent wraparound in non-ANSI mode"],
     ["INT for a and b is fine at current values", "the 10+20 row is not the problem"],
     "Widen to BIGINT before adding, or use try_add and handle NULL explicitly; decide the policy, "
     "do not inherit it from spark.sql.ansi.enabled.",
     "flaw.sql throws ARITHMETIC_OVERFLOW under this session (ANSI on); the df variants show the same "
     "query silently WRAPPING to -2147483648 with ANSI off (Java-style int overflow, not NULL); "
     "try_add returns NULL for row 1 and 30 for row 2.",
     "q20: 2 rows; row 1 holds INT_MAX + 1 as two INTs.",
     dfv=["spark.conf.set('spark.sql.ansi.enabled','false')",
          "spark.sql('SELECT id, a + b FROM q20').collect()",
          "spark.conf.set('spark.sql.ansi.enabled','true')"])

case("21", "divide-by-zero-no-guard", "easy", "correctness", "021",
     "A rate column divides by a counter that is 0 for real rows.",
     ["CREATE OR REPLACE TEMP VIEW q21 AS SELECT * FROM VALUES (10, 2), (10, 0) AS t(n, d)"],
     "SELECT n / d FROM q21",
     "SELECT n / NULLIF(d, 0) FROM q21",
     ["division without a zero guard", "zero divisor possible per data"],
     ["returning NULL for the zero row is an acceptable policy once explicit", "the 10/2 row is fine"],
     "Guard the divisor: n / NULLIF(d, 0) (or try_divide) so the zero row yields a handled NULL instead "
     "of a job-killing exception (ANSI) or a silent NULL you never chose (non-ANSI).",
     "flaw.sql throws DIVIDE_BY_ZERO in this session (ANSI on); the df variants show the same statement "
     "returning NULL with ANSI off; fixed.sql returns [5.0, NULL].",
     "q21: 2 rows; d=0 occurs once.",
     dfv=["spark.conf.set('spark.sql.ansi.enabled','false')",
          "spark.sql('SELECT n / d FROM q21').collect()",
          "spark.conf.set('spark.sql.ansi.enabled','true')"])

case("24", "ansi-default-upgrade-flip", "hard", "maintainability", "024",
     "A dirty-code CAST job ran for years on Spark 3; after the Spark 4 upgrade the same jar dies at runtime.",
     ["CREATE OR REPLACE TEMP VIEW q24 AS SELECT * FROM VALUES ('12'), ('7'), ('12x'), "
      "(CAST(NULL AS STRING)) AS t(code)"],
     "SELECT CAST(code AS INT) FROM q24",
     "SELECT try_cast(code AS INT) FROM q24",
     ["behavior differs between Spark 3 and Spark 4 for the same query", "ANSI default flipped in Spark 4",
      "unguarded cast on dirty codes", "spark.sql.ansi.enabled decides between NULL and exception"],
     ["pure-digit codes cast fine", "try_cast returning NULL for '12x' is the intended policy"],
     "Audit casts and arithmetic against ANSI semantics before upgrading: use try_cast/try_add/NULLIF so "
     "behaviour is pinned by the query, not by spark.sql.ansi.enabled (see repro/outputs/000-cross-spark3.txt "
     "vs 000-cross-spark4.txt and 024-ansi-mode-3-vs-4.txt).",
     "flaw.sql throws in this Spark 4.2 session; the df variants show it returning NULL silently with ANSI "
     "off (the Spark 3.5 default - 000-cross-spark3.txt); try_cast returns [12, 7, NULL, NULL] under both modes.",
     "q24: 4 codes, one non-numeric ('12x'), one NULL.",
     dfv=["spark.conf.set('spark.sql.ansi.enabled','false')",
          "spark.sql('SELECT CAST(code AS INT) FROM q24').collect()",
          "spark.sql('SELECT try_cast(code AS INT) FROM q24').collect()",
          "spark.conf.set('spark.sql.ansi.enabled','true')"])

case("31", "csv-inferschema-loses-leading-zeros", "medium", "correctness", "031",
     "A CSV import with inferSchema=True silently turns codes '001' into 1 and the downstream join finds nothing.",
     ["CREATE OR REPLACE TEMP VIEW q31dim AS SELECT * FROM VALUES ('001','Gold'), ('010','Silver') AS t(code, tier)"],
     "-- PySpark job: spark.read.option('header','true').option('inferSchema','true')"
     ".csv('31-csv-inferschema-loses-leading-zeros/data.csv').join(spark.table('q31dim'), 'code')\n"
     "SELECT * FROM q31dim",
     "-- spark.read.option('header','true').schema('code STRING, name STRING')"
     ".csv('31-csv-inferschema-loses-leading-zeros/data.csv')\n"
     "SELECT code, tier FROM q31dim WHERE code IN ('001', '010')",
     ["inferSchema turns leading-zero codes into INT", "codes corrupted before the join", "schema must be explicit"],
     ["CSV with header=True is fine", "the dimension table itself is correct"],
     "Pass an explicit schema (code STRING, name STRING) instead of inferSchema for code-like columns "
     "(see repro/outputs/031).",
     "df variants: the inferSchema read reports code:int and values [1, 2, 10] (join with '001' impossible); "
     "the explicit-schema read keeps ['001','002','010'] and joins to the dim.",
     "data.csv: 3 rows, codes 001/002/010; dim: 2 tiers keyed by the string codes.",
     dfv=["spark.read.option('header','true').option('inferSchema','true')"
          ".csv('31-csv-inferschema-loses-leading-zeros/data.csv').schema.simpleString()",
          "spark.read.option('header','true').option('inferSchema','true')"
          ".csv('31-csv-inferschema-loses-leading-zeros/data.csv').collect()",
          "spark.read.option('header','true').schema('code STRING, name STRING')"
          ".csv('31-csv-inferschema-loses-leading-zeros/data.csv').collect()"],
     extras={"data.csv": "code,name\n001,Alice\n002,Bob\n010,Carol\n"})

case("35", "like-case-portability", "easy", "correctness", "035",
     "A 'starts with a' filter ported from sqlite misses 'Apple' on Spark.",
     ["CREATE OR REPLACE TEMP VIEW q35 AS SELECT * FROM VALUES ('Apple'), ('apple'), ('apricot'), "
      "('Banana') AS t(fruit)"],
     "SELECT fruit FROM q35 WHERE fruit LIKE 'a%'",
     "SELECT fruit FROM q35 WHERE lower(fruit) LIKE 'a%'",
     ["LIKE is case-sensitive in Spark", "porting from sqlite or MySQL changes the result set"],
     ["filtering to a-prefix fruits is the goal", "Banana is correctly excluded"],
     "Normalise both sides (lower(fruit) LIKE 'a%') or use an explicit collation, so the predicate means "
     "the same thing on every engine (see repro/outputs/035 for the sqlite/DuckDB comparison).",
     "flaw.sql returns 2 rows (apple, apricot); fixed.sql returns 3 (Apple, apple, apricot).",
     "q35: 4 fruits; one capital-A row.")

case("36", "shuffle-partitions-default-200", "hard", "performance", "-",
     "A 10k-row nightly aggregation ships with the cluster default 200 shuffle partitions.",
     ["CREATE OR REPLACE TEMP VIEW q36 AS SELECT id, id % 50 AS k, lpad(CAST(id AS STRING), 60, 'x') AS pad "
      "FROM range(10000)"],
     "-- runs with the session default spark.sql.shuffle.partitions (200 on the cluster)\n"
     "SELECT k, count(*), max(pad) FROM q36 GROUP BY k",
     "-- set spark.sql.shuffle.partitions=8 (or size it) before this job\n"
     "SELECT k, count(*), max(pad) FROM q36 GROUP BY k",
     ["default 200 shuffle partitions for 10k rows", "199 nearly-empty tasks per stage",
      "spark.sql.shuffle.partitions not sized", "AQE coalescing not verified"],
     ["GROUP BY k is the right shape", "50 groups is not the problem"],
     "Size spark.sql.shuffle.partitions to the data (single digits for 10k rows) or rely on AQE "
     "coalescing deliberately, after checking it is on; keep 200 only when the upstream shuffle is big.",
     "df variants: with AQE off and the default 200, a hash shuffle of q36 (repartition by k) yields 200 "
     "partitions of ~50 rows; setting 8 yields 8. With AQE ON (the default) the same shuffle is coalesced "
     "to 1 output partition - observed - but the 200 shuffle blocks are still written first. Also note: "
     "on this local[1] session the tiny GROUP BY plan needs no Exchange at all (single input split).",
     "q36: 10000 rows, 50 groups (~200 rows/group, ~60-byte pad).",
     dfv=["spark.conf.set('spark.sql.adaptive.enabled','false')",
          "spark.conf.set('spark.sql.shuffle.partitions','200')",
          "spark.table('q36').repartition('k').rdd.getNumPartitions()",
          "spark.conf.set('spark.sql.shuffle.partitions','8')",
          "spark.table('q36').repartition('k').rdd.getNumPartitions()",
          "spark.conf.set('spark.sql.shuffle.partitions','4')",
          "spark.conf.set('spark.sql.adaptive.enabled','true')"])

case("37", "select-star-through-join", "hard", "cost", "-",
     "An enrichment join selects * and carries 10 unused 180-byte columns through the shuffle; downstream reads two.",
     ["CREATE OR REPLACE TEMP VIEW q37 AS SELECT id AS k, id % 40 AS d, "
      "lpad(CAST(id AS STRING), 180, 'x') AS payload_a, lpad(CAST(id AS STRING), 180, 'x') AS payload_b, "
      "lpad(CAST(id AS STRING), 180, 'x') AS payload_c, lpad(CAST(id AS STRING), 180, 'x') AS payload_d, "
      "lpad(CAST(id AS STRING), 180, 'x') AS payload_e, lpad(CAST(id AS STRING), 180, 'x') AS payload_f, "
      "lpad(CAST(id AS STRING), 180, 'x') AS payload_g, lpad(CAST(id AS STRING), 180, 'x') AS payload_h, "
      "lpad(CAST(id AS STRING), 180, 'x') AS payload_i, lpad(CAST(id AS STRING), 180, 'x') AS payload_j "
      "FROM range(20000)",
      "CREATE OR REPLACE TEMP VIEW q37dim AS SELECT id AS d, concat('tier-', id) AS tier FROM range(40)"],
     "SELECT * FROM q37 JOIN q37dim USING (d)",
     "SELECT q37.k, q37dim.tier FROM q37 JOIN q37dim ON q37.d = q37dim.d",
     ["SELECT * through a shuffle join", "unused wide columns carried into the join", "column pruning defeated"],
     ["the join on d is correct", "USING/ON style is a style choice, not the defect"],
     "Project the columns downstream needs before the join (q37.k, q37dim.tier) so the scan prunes and "
     "the shuffle carries ~4% of the bytes.",
     "df variants: the executed plan of the flaw mentions payload_* columns (>0 lines); the fixed plan "
     "mentions none (0). Shuffle cost ~20000 x 10 x 180B = 36 MB vs <1 MB.",
     "q37: 20000 rows, 2 key cols + 10 payloads of 180 chars; q37dim: 40 rows, tiny.",
     dfv=["sum(1 for l in spark.sql('SELECT * FROM q37 JOIN q37dim USING (d)')"
          "._jdf.queryExecution().executedPlan().toString().splitlines() if 'payload_j' in l)",
          "sum(1 for l in spark.sql('SELECT q37.k, q37dim.tier FROM q37 JOIN q37dim ON q37.d = q37dim.d')"
          "._jdf.queryExecution().executedPlan().toString().splitlines() if 'payload_j' in l)"])

case("38", "repartition-before-single-write", "hard", "performance", "-",
     "A job repartition(100)s 50k rows before writing Parquet for a single-file consumer.",
     ["CREATE OR REPLACE TEMP VIEW q38 AS SELECT id, id % 20 AS k, lpad(CAST(id AS STRING), 100, 'p') AS pad "
      "FROM range(50000)"],
     "-- PySpark job: spark.table('q38').repartition(100).write.mode('overwrite').parquet('out/')\n"
     "-- consumed by a single-file loader\nSELECT count(*) FROM q38",
     "-- PySpark job: spark.table('q38').coalesce(1).write.mode('overwrite').parquet('out/')\n"
     "SELECT count(*) FROM q38",
     ["repartition(100) adds a full shuffle before a single-file write", "100 small files for one consumer"],
     ["repartition itself is a valid tool at other scales", "50k rows is not the issue"],
     "Use coalesce(1) (no shuffle) for a single-file sink, or size the partition count to the consumer; "
     "repartition only when an even spread is worth a full shuffle.",
     "df variants: repartition(100).rdd.getNumPartitions() = 100 (a full hash shuffle); "
     "coalesce(1).rdd.getNumPartitions() = 1 with no shuffle stage.",
     "q38: 50000 rows, 100-byte pad, 20 distinct k.",
     dfv=["spark.table('q38').repartition(100).rdd.getNumPartitions()",
          "spark.table('q38').coalesce(1).rdd.getNumPartitions()"])

case("39", "skew-join-no-broadcast", "hard", "performance", "-",
     "90% of a fact table sits on key 0 and joins a padded dimension with no broadcast hint.",
     ["CREATE OR REPLACE TEMP VIEW q39 AS SELECT id, CASE WHEN id < 18000 THEN 0 ELSE id END AS k "
      "FROM range(20000)",
      "CREATE OR REPLACE TEMP VIEW q39dim AS SELECT k, label, lpad(label, 3000000, 'z') AS pad FROM VALUES "
      "(0, 'hot'), (1, 'a'), (2, 'b'), (3, 'c'), (4, 'd') AS t(k, label)"],
     "SELECT q39dim.label, count(*) AS n FROM q39 JOIN q39dim ON q39.k = q39dim.k GROUP BY q39dim.label",
     "SELECT /*+ BROADCAST(q39dim) */ q39dim.label, count(*) AS n FROM q39 JOIN q39dim ON q39.k = q39dim.k "
     "GROUP BY q39dim.label",
     ["skewed join key", "join strategy not pinned", "one straggler task processes the hot key",
      "planner picks broadcast or sort-merge depending on stats and threshold"],
     ["the CASE WHEN generating k is fine", "GROUP BY label is fine"],
     "Pin the join strategy for a dimension that fits memory: /*+ BROADCAST(q39dim) */, or split the "
     "hot key (salt + aggregate twice); check the join type in the plan, not the wall clock on tiny data.",
     "df variants: at the default 10 MB auto-broadcast threshold the unhinted plan HAPPENS to pick "
     "BroadcastHashJoin on this data (stats do not price the lpad width) - the strategy floats with "
     "data size and config; with the threshold disabled (simulating a dimension too big to broadcast) "
     "the unhinted query falls to SortMergeJoin on a 90%-skewed key while the hinted query still "
     "broadcasts. Timing on 20k local rows is noise - the mechanism is plan shape + the 90/10 split.",
     "q39: 20000 rows, 18000 on k=0; q39dim: 5 rows padded to ~3 MB each (~15 MB).",
     dfv=["sum(1 for l in spark.sql('SELECT q39dim.label, count(*) AS n FROM q39 JOIN q39dim ON q39.k = q39dim.k "
          "GROUP BY q39dim.label')._jdf.queryExecution().executedPlan().toString().splitlines() "
          "if 'SortMergeJoin' in l)",
          "sum(1 for l in spark.sql('SELECT /*+ BROADCAST(q39dim) */ q39dim.label, count(*) AS n FROM q39 "
          "JOIN q39dim ON q39.k = q39dim.k GROUP BY q39dim.label')"
          "._jdf.queryExecution().executedPlan().toString().splitlines() if 'BroadcastHashJoin' in l)",
          "spark.conf.set('spark.sql.autoBroadcastJoinThreshold','-1')",
          "sum(1 for l in spark.sql('SELECT q39dim.label, count(*) AS n FROM q39 JOIN q39dim ON q39.k = q39dim.k "
          "GROUP BY q39dim.label')._jdf.queryExecution().executedPlan().toString().splitlines() "
          "if 'SortMergeJoin' in l)",
          "sum(1 for l in spark.sql('SELECT /*+ BROADCAST(q39dim) */ q39dim.label, count(*) AS n FROM q39 "
          "JOIN q39dim ON q39.k = q39dim.k GROUP BY q39dim.label')"
          "._jdf.queryExecution().executedPlan().toString().splitlines() if 'BroadcastHashJoin' in l)",
          "spark.conf.set('spark.sql.autoBroadcastJoinThreshold','10485760b')"])

case("40", "collect-to-driver", "hard", "cost", "-",
     "A job collect()s 100k rows to the driver to sum one column in Python.",
     ["CREATE OR REPLACE TEMP VIEW q40 AS SELECT id, (id % 100) AS grp, lpad(CAST(id AS STRING), 50, 'x') "
      "AS pad FROM range(100000)"],
     "-- PySpark job: rows = spark.table('q40').collect(); total = sum(r['id'] for r in rows)\n"
     "SELECT * FROM q40",
     "-- PySpark job: total = spark.table('q40').agg(F.sum('id')).collect()[0][0]\n"
     "SELECT sum(id) FROM q40",
     ["collect() pulls all rows to the driver", "aggregation done in Python instead of the engine",
      "driver memory and serialization cost"],
     ["summing id is a fine goal", "100k rows is not the issue at this scale - the pattern is"],
     "Push the aggregation into Spark (agg(F.sum('id'))) and collect only the result row; collect() only "
     "small, bounded results.",
     "df variants print (row count, milliseconds): collect()+Python loop vs a single aggregate - on this "
     "local[1] session the collect variant takes a multiple of the aggregate's time and both timings are "
     "single-run observations, not a cluster claim.",
     "q40: 100000 rows, 50-byte pad (~10 MB moved to the driver).",
     dfv=["(lambda t0: (len(spark.table('q40').collect()), "
          "round((__import__('time').time() - t0) * 1000)))(__import__('time').time())",
          "(lambda t0: (spark.table('q40').agg(F.sum('id')).collect(), "
          "round((__import__('time').time() - t0) * 1000)))(__import__('time').time())"])


def main() -> None:
    for c in C:
        d = HERE / f"{c['n']}-{c['name']}"
        d.mkdir(exist_ok=True)
        (d / "gen.sql").write_text(";\n".join(c["gen"]) + ";\n", encoding="utf-8")
        (d / "flaw.sql").write_text(c["flaw"] + ";\n", encoding="utf-8")
        (d / "fixed.sql").write_text(c["fixed"] + ";\n", encoding="utf-8")
        (d / "prompt.md").write_text(
            f"# Case {c['n']}: {c['name']} (difficulty: {c['difficulty']})\n\n"
            f"{c['intro']}\n\n## Schema and data (gen.sql)\n"
            + "```sql\n" + ";\n".join(c["gen"]) + ";\n" + "```\n\n"
            f"## Statistics\n{c['stats']}\n\n"
            "## Query under review\n```sql\n" + c["flaw"] + ";\n```\n\n"
            "Also see plan.txt (EXPLAIN of the query on this data).\n\n"
            "## Your task\nList every defect you can defend (correctness, performance, cost, maintainability), "
            "the mechanism, and the minimal fix. Do not invent data properties not shown above.\n",
            encoding="utf-8")
        (d / "answer.md").write_text(
            f"# Key {c['n']} (HIDDEN FROM REVIEWER)\n\n"
            f"Defect (category: {c['category']}, from pitfall {c['pitfall']}): see repro/outputs/{c['pitfall']}-*.txt.\n\n"
            f"## Required findings (any one term suffices per line)\n"
            + "```required_findings\n" + "\n".join(" | ".join(t.split(" or ")) for t in c["defects"]) + "\n```\n\n"
            "## Decoys (count as false claims if reported as defects)\n"
            + "```non_defects\n" + "\n".join(c["non_defects"]) + "\n```\n\n"
            f"## Expected fix\n{c['fix']}\n\n## How to check the fix by running\n{c['verify']}\n"
            "Run with: ../venv/py4/bin/python ../repro-style runner or cases/verify_all.py --only "
            f"{c['n']} (from cases/).\n",
            encoding="utf-8")
        meta = {k: c[k] for k in ("n", "name", "difficulty", "category", "pitfall", "variants")}
        meta["required_findings"] = c["defects"]
        meta["non_defects"] = c["non_defects"]
        meta["df_variants"] = c["dfv"]
        (d / "case.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
        for fn, content in c["extras"].items():
            (d / fn).write_text(content, encoding="utf-8")
    print(f"built {len(C)} cases under {HERE}")


if __name__ == "__main__":
    main()
