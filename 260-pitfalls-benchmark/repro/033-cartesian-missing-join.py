#!/usr/bin/env python
"""Standalone runner for pitfall 033: Missing join condition turns the query into a cartesian product
Run: ../venv/py4/bin/python 033-cartesian-missing-join.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '033'])
