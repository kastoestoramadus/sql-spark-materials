#!/usr/bin/env python
"""Standalone runner for pitfall 005: WHERE on the right side of a LEFT JOIN kills unmatched rows
Run: ../venv/py4/bin/python 005-outer-join-where-vs-on.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '005'])
