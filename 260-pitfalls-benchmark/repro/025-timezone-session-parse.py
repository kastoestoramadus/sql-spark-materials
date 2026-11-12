#!/usr/bin/env python
"""Standalone runner for pitfall 025: Same timestamp string parses to different instants per session time zo
Run: ../venv/py4/bin/python 025-timezone-session-parse.py  (from repro/)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_all
run_all.main(argv=[sys.argv[0], '--only', '025'])
