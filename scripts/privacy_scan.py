#!/usr/bin/env python3
"""Deprecated compatibility wrapper. Use release_safety_scan.py instead."""
from __future__ import annotations
import subprocess, sys
from pathlib import Path

if __name__ == "__main__":
    target = Path(__file__).with_name("release_safety_scan.py")
    raise SystemExit(subprocess.call([sys.executable, str(target), *sys.argv[1:], "--strict-personal"]))
