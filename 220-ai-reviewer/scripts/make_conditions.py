#!/usr/bin/env python
"""Generate the four reading conditions for each case: compact plan and sqlglot AST dumps.

Condition files (sql and explain-* already written by make_plans.py):
  <case>/compact.txt   - compact_plan.py digest of explain-extended.txt
  <case>/ast.txt       - sqlglot AST dump (parse sql with spark dialect)
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import sqlglot

R = Path(__file__).resolve().parent.parent
CASES = R / "artifacts" / "cases"


def sql_of(case_dir: Path) -> str:
    txt = (case_dir / "question.txt").read_text(encoding="utf-8")
    m = re.search(r"\n\n(.*)\n?$", txt, re.S)
    return m.group(1).strip() if m else ""


def main() -> int:
    n_ast = n_compact = 0
    for d in sorted(CASES.iterdir()):
        if not d.is_dir():
            continue
        sql = sql_of(d)
        try:
            tree = sqlglot.parse_one(sql, dialect="spark")
            (d / "ast.txt").write_text(repr(tree), encoding="utf-8")
            n_ast += 1
        except Exception as e:  # noqa: BLE001 - record failure per case, keep going
            (d / "ast.txt").write_text(f"PARSE ERROR: {e}", encoding="utf-8")
        res = subprocess.run([sys.executable, str(R / "scripts" / "compact_plan.py"), str(d / "explain-extended.txt")],
                             capture_output=True, text=True, check=True)
        (d / "compact.txt").write_text(res.stdout, encoding="utf-8")
        n_compact += 1
    print(f"ast dumps: {n_ast}, compact dumps: {n_compact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
