#!/usr/bin/env python
"""Standalone runner for pitfall 009: dropDuplicates keeps an arbitrary row per key
Run: ../venv/py4/bin/python 009-dropduplicates-arbitrary-row.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '009'])
