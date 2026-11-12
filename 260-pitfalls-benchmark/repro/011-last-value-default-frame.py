#!/usr/bin/env python
"""Standalone runner for pitfall 011: LAST_VALUE with the default frame returns the current row
Run: ../venv/py4/bin/python 011-last-value-default-frame.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '011'])
