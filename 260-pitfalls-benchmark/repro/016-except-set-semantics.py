#!/usr/bin/env python
"""Standalone runner for pitfall 016: EXCEPT drops duplicates of the left side (set vs multiset)
Run: ../venv/py4/bin/python 016-except-set-semantics.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '016'])
