#!/usr/bin/env python3
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

def _load_env_local():
    """Load key=value pairs from .env.local into os.environ if not already set.
    Avoids external dependencies (python-dotenv).
    """
    candidates = [Path.cwd() / ".env.local", Path(__file__).resolve().parent / ".env.local"]
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
            # Non-fatal; continue without env file
            pass

_load_env_local()

from a2a.cli import main

if __name__ == "__main__":
    main()
