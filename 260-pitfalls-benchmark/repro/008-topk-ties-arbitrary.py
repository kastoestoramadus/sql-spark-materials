#!/usr/bin/env python
"""Standalone runner for pitfall 008: Top-K with ties on ORDER BY picks arbitrary rows
Run: ../venv/py4/bin/python 008-topk-ties-arbitrary.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '008'])
