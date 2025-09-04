#!/usr/bin/env python3
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from a2a.cli import main

if __name__ == "__main__":
    main()

