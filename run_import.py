#!/usr/bin/env python3
"""
Wrapper to run import_wal33d_dtc.py with proper encoding
"""
import sys
import os

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Add --yes flag if not present
if "--yes" not in sys.argv and "-y" not in sys.argv:
    sys.argv.append("--yes")

# Import and run the actual script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from import_wal33d_dtc import main

if __name__ == "__main__":
    sys.exit(main())
