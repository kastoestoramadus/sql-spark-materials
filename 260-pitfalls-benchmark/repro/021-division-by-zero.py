#!/usr/bin/env python
"""Standalone runner for pitfall 021: 1/0: Spark NULL (non-ANSI) or exception (ANSI); DuckDB inf; sqlite NUL
Run: ../venv/py4/bin/python 021-division-by-zero.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '021'])
