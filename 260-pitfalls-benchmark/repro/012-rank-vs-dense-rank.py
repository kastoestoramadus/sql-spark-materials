#!/usr/bin/env python
"""Standalone runner for pitfall 012: RANK gaps after ties vs DENSE_RANK; ROW_NUMBER is arbitrary on ties
Run: ../venv/py4/bin/python 012-rank-vs-dense-rank.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '012'])
