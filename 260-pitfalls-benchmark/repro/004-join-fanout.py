#!/usr/bin/env python
"""Standalone runner for pitfall 004: Duplicate join keys fan out rows and inflate aggregates
Run: ../venv/py4/bin/python 004-join-fanout.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '004'])
