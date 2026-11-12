#!/usr/bin/env python
"""Standalone runner for pitfall 027: to_timestamp with wrong pattern returns NULL for all rows
Run: ../venv/py4/bin/python 027-timestamp-format-silent-null.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '027'])
