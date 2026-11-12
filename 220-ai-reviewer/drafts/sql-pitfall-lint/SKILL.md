---
name: sql-pitfall-lint
description: Use before any human or model review of SQL, to run deterministic checks for known LLM/author pitfalls: joins without column-to-column equality (cartesian risk), NOT IN over subqueries, NULL-dropping != filters, outer joins defeated by WHERE filters, COUNT DISTINCT NULL exclusion, to_date format traps, leading-wildcard LIKE, integer division. Works on a file of SQL in any of sqlglot's 30+ dialects; pin the dialect explicitly. Not a semantic proof - its output is a checklist for reasoning, not a verdict.
---

# SQL pitfall lint

## When to use
- First contact with a query under review; runs in milliseconds, needs only Python (sqlglot wheel, no JVM).
- Before transpiling between dialects (Hive -> Spark SQL at the bank): parse errors surface here first.

## Steps
1. `python scripts/lint_sql.py <file.sql> --dialect spark` (dialect is mandatory knowledge: hive vs spark
   vs an RDBMS changes semantics; if unknown, run all candidates and report which parsed).
2. Findings are `severity<TAB>check<TAB>message`. HIGH = verify before trusting the query
   (no-equi-join, outer-join-defeated, not-in-subquery, parse-error). INFO = NULL-semantics decisions
   (neq-null, count-distinct-null, to-date-format, leading-wildcard-like, int-div).
3. A parse error is a finding, not a crash: report exactly what failed to parse in which dialect.
4. For every HIGH finding, check it against the plan if one exists (skill `spark-plan-review`):
   the cartesian lint (fired on q01, task 220) is confirmed by a CartesianProduct node in the plan.

## Validated behaviour (task 220 run, 2026-10-18)
- Fired: q01 no-equi-join, q02 outer-join-defeated, q03 not-in-subquery, q04 neq-null.
- Correctly silent: q07 (window), q10 (fanout) - these are semantic/perf, left to reasoning + plan.
- sqlglot version pinned in scripts: 30.x; AST repr format differs across sqlglot majors.

## Blind spots
- No schema: cannot know nullability, so NULL checks are advisory, not proven.
- Join fanout double-counting (q10) and unpartitioned windows (q07) are NOT linted - they need the plan.

## Privacy
Pure local execution; nothing leaves the machine.
