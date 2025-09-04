#!/usr/bin/env python3
import sys
from pathlib import Path

# Ensure repo root is on sys.path
root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from a2a.cli import main as _main

# Temporary shim to maintain compatibility after rename to A2Dev
def main():
    _main()

if __name__ == "__main__":
    main()
