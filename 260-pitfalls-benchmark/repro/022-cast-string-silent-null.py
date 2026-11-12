#!/usr/bin/env python
"""Standalone runner for pitfall 022: CAST('abc' AS INT): Spark NULL, DuckDB error, sqlite 0 — silent row lo
Run: ../venv/py4/bin/python 022-cast-string-silent-null.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '022'])
