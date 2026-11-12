#!/usr/bin/env python
"""Standalone runner for pitfall 007: LIMIT without ORDER BY returns arbitrary rows
Run: ../venv/py4/bin/python 007-limit-without-order.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '007'])
