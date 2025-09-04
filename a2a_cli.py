#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path
root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

def _load_env_local():
    candidates = [Path.cwd() / ".env.local", root / ".env.local"]
    for p in candidates:
        try:
            if not p.exists():
                continue
            for raw in p.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                os.environ.setdefault(k, v)
        except Exception:
            pass

_load_env_local()

from a2a.cli import main as _main

# Temporary shim to maintain compatibility after rename to A2Dev
def main():
    _main()

if __name__ == "__main__":
    main()
