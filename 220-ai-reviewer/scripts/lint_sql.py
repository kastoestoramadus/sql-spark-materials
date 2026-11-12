#!/usr/bin/env python
"""Deterministic SQL pitfall linter for AI reviewers (sqlglot-based, no Spark needed).

Checks are heuristics over the AST: they FLAG, they do not prove. Output rows:
severity, check id, location, message. Exit 0 always (findings are data, not errors).
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Iterator

import sqlglot
from sqlglot import exp


def right_aliases(select: exp.Select) -> set[str]:
    """Aliases of tables joined with LEFT/RIGHT/FULL in this select."""
    out: set[str] = set()
    for j in select.find_all(exp.Join):
        if j.side in ("LEFT", "RIGHT", "FULL"):
            for t in j.find_all(exp.Table):
                if t.alias_or_name:
                    out.add(t.alias_or_name)
    return out


def checks(tree: exp.Expr) -> Iterator[tuple[str, str, str]]:
    for node in tree.walk():
        n = node[0] if isinstance(node, tuple) else node
        if isinstance(n, exp.In) and isinstance(n.parent, exp.Not) and n.args.get("query"):
            yield ("HIGH", "not-in-subquery", "NOT IN over subquery: empty result if the selected column has any NULL - verify NOT NULL or use NOT EXISTS")
        if isinstance(n, (exp.NEQ,)):
            yield ("INFO", "neq-null", "!= drops NULL rows on both sides; if NULLs exist add IS NULL handling")
        if isinstance(n, exp.Join):
            on = n.args.get("on")
            eqs = list(on.find_all(exp.EQ)) if on is not None else []
            col_on_col = [e for e in eqs if e.this.find(exp.Column) and e.expression.find(exp.Column)]
            if on is None or not eqs or not col_on_col:
                yield ("HIGH", "no-equi-join", "join without column-to-column equality: cartesian/nested-loop product (constant-only ON conditions do not count)")
        if isinstance(n, exp.Count) and isinstance(n.this, exp.Distinct):
            yield ("INFO", "count-distinct-null", "COUNT(DISTINCT x) excludes NULL x - state whether that is intended")
        if isinstance(n, exp.Anonymous) and n.sql().lower().startswith("to_date"):
            yield ("INFO", "to-date-format", "to_date with format: NULL for every row whose stored format differs")
        if isinstance(n, exp.Like) and isinstance(n.expression, exp.Literal):
            v = n.expression.this
            if isinstance(v, str) and v.startswith("%"):
                yield ("INFO", "leading-wildcard-like", "LIKE '%...' cannot use prefix pushdown; full scan of that predicate")
        if isinstance(n, exp.IntDiv):
            yield ("INFO", "int-div", "integer DIV truncates; '/' returns fractional - pick deliberately")
    for select in tree.find_all(exp.Select):
        ra = right_aliases(select)
        if not ra:
            continue
        for w in select.args.get("where", []).find_all(exp.Column) if select.args.get("where") else []:
            pass
        where = select.args.get("where")
        if where is None:
            continue
        for col in where.find_all(exp.Column):
            if col.table in ra:
                isnull_guard = any(isinstance(p, exp.Is) for p in col.find_ancestors(exp.Is)) if hasattr(col, "find_ancestors") else False
                if not isnull_guard:
                    yield ("INFO", "outer-join-null-review", f"WHERE references '{col.table}.' from an outer join: inspect whether the full predicate accepts NULL; join simplification is not proven")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("infile")
    ap.add_argument("--dialect", default="spark")
    args = ap.parse_args()
    sql = open(args.infile, encoding="utf-8").read()
    try:
        tree = sqlglot.parse_one(sql, dialect=args.dialect)
    except sqlglot.errors.ParseError as e:
        print(f"HIGH\tparse-error\tn/a\tquery does not parse in {args.dialect}: {e}")
        return 0
    for sev, cid, msg in sorted(set(checks(tree))):
        print(f"{sev}\t{cid}\t{msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
