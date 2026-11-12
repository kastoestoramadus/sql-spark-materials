#!/usr/bin/env python
"""Standalone runner for pitfall 023: Comparing string column to number silently casts (and silently drops)
Run: ../venv/py4/bin/python 023-implicit-cast-compare.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '023'])
