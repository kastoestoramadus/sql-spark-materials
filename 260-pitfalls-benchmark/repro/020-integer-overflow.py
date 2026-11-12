#!/usr/bin/env python
"""Standalone runner for pitfall 020: Integer overflow: NULL silently (non-ANSI), exception (ANSI), try_add 
Run: ../venv/py4/bin/python 020-integer-overflow.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '020'])
