#!/usr/bin/env python
"""Standalone runner for pitfall 026: DST gap/overlap wall-clock times are shifted or ambiguous
Run: ../venv/py4/bin/python 026-timezone-dst-gap.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '026'])
