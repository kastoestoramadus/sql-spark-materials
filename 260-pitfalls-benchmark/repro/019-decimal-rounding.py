#!/usr/bin/env python
"""Standalone runner for pitfall 019: HALF_UP vs HALF_EVEN rounding disagree across Spark round/bround, cast
Run: ../venv/py4/bin/python 019-decimal-rounding.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '019'])
