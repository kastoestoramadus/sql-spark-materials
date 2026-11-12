#!/usr/bin/env python
"""Standalone runner for pitfall 013: Unseeded rand() re-evaluates per action; two actions disagree
Run: ../venv/py4/bin/python 013-rand-nondeterministic.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '013'])
