#!/usr/bin/env python
"""Standalone runner for pitfall 001: = NULL never matches; NULL = NULL is NULL
Run: ../venv/py4/bin/python 001-null-equality.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '001'])
