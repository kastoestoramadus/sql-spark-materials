#!/usr/bin/env python
"""Standalone runner for pitfall 034: sortWithinPartitions is not a global ORDER BY
Run: ../venv/py4/bin/python 034-sort-within-partitions.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '034'])
