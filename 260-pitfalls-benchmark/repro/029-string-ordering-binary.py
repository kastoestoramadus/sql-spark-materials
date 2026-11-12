#!/usr/bin/env python
"""Standalone runner for pitfall 029: String ORDER BY is binary codepoint order, not locale/collation order
Run: ../venv/py4/bin/python 029-string-ordering-binary.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '029'])
