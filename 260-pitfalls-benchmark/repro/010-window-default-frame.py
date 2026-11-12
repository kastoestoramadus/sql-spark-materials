#!/usr/bin/env python
"""Standalone runner for pitfall 010: Ordered window defaults to RANGE frame: peers share the running total
Run: ../venv/py4/bin/python 010-window-default-frame.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '010'])
