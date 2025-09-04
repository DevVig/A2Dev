#!/usr/bin/env python3
import os
import shutil
import sys
import zipapp
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT / "a2dev.pyz"
    # Ensure a __main__ is resolvable via a module path
    # We point to a2a.cli:main
    zipapp.create_archive(str(ROOT), str(target), main="a2a.cli:main", interpreter=sys.executable)
    print(f"Built {target}")


if __name__ == "__main__":
    main()

