#!/usr/bin/env python
"""Standalone runner for pitfall 024: ANSI/cast/overflow behaviour differs by version and spark.sql.ansi.ena
Run: ../venv/py4/bin/python 024-ansi-mode-3-vs-4.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '024'])
