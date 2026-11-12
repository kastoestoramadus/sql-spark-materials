#!/usr/bin/env python
"""Standalone runner for pitfall 032: User input inside LIKE: % and _ act as wildcards
Run: ../venv/py4/bin/python 032-like-pattern-injection.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '032'])
