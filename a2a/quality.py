from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple


def semgrep_summary(path: Path) -> Tuple[int, int, int]:
    if not path.exists():
        return 0, 0, 0
    try:
        data = json.loads(path.read_text())
    except Exception:
        return 0, 0, 0
    findings = data.get("results", [])
    high = sum(1 for r in findings if r.get("extra", {}).get("severity") in ("ERROR", "HIGH"))
    med = sum(1 for r in findings if r.get("extra", {}).get("severity") in ("WARNING", "MEDIUM"))
    low = sum(1 for r in findings if r.get("extra", {}).get("severity") in ("INFO", "LOW"))
    return high, med, low

