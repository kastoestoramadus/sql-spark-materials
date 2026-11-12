#!/usr/bin/env python
"""Standalone runner for pitfall 003: Join keys with NULLs are silently dropped (=) but kept with <=>
Run: ../venv/py4/bin/python 003-join-null-keys.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '003'])
