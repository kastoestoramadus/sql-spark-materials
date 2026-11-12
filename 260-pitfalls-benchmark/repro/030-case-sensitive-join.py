#!/usr/bin/env python
"""Standalone runner for pitfall 030: Join keys differing only in case match nothing (= is case-sensitive)
Run: ../venv/py4/bin/python 030-case-sensitive-join.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '030'])
