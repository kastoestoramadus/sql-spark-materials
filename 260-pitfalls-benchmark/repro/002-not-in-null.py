#!/usr/bin/env python
"""Standalone runner for pitfall 002: NOT IN with NULL in the subquery returns nothing
Run: ../venv/py4/bin/python 002-not-in-null.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '002'])
