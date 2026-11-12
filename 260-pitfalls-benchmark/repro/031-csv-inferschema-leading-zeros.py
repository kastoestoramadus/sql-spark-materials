#!/usr/bin/env python
"""Standalone runner for pitfall 031: CSV inferSchema turns '001' into 1: leading zeros lost, joins fail
Run: ../venv/py4/bin/python 031-csv-inferschema-leading-zeros.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '031'])
