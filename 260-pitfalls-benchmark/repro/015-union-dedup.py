#!/usr/bin/env python
"""Standalone runner for pitfall 015: UNION deduplicates by default (semantics + hidden shuffle cost)
Run: ../venv/py4/bin/python 015-union-dedup.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '015'])
