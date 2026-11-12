#!/usr/bin/env python
"""Standalone runner for pitfall 017: SUM over DOUBLE depends on partitioning (float addition is not associa
Run: ../venv/py4/bin/python 017-float-sum-order.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '017'])
