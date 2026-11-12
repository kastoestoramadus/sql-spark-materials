#!/usr/bin/env python
"""Standalone runner for pitfall 028: Jan 31 + INTERVAL 1 MONTH clamps to Feb 28 silently
Run: ../venv/py4/bin/python 028-date-month-end-clamp.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '028'])
