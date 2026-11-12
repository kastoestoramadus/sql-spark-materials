#!/usr/bin/env python
"""Standalone runner for pitfall 018: DECIMAL(38,*) arithmetic silently overflows to NULL
Run: ../venv/py4/bin/python 018-decimal-precision-null.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '018'])
