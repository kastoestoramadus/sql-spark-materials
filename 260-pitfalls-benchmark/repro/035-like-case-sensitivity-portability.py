#!/usr/bin/env python
"""Standalone runner for pitfall 035: LIKE case sensitivity differs: sqlite insensitive, Spark/DuckDB sensit
Run: ../venv/py4/bin/python 035-like-case-sensitivity-portability.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '035'])
