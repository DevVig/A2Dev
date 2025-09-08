#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def run_benchmark(story_id: int) -> dict:
    # Ensure import path for a2a
    sys.path.insert(0, str(Path.cwd()))
    os.environ.setdefault("A2DEV_MODE", os.environ.get("A2DEV_MODE", "off"))
    from scripts.benchmark import _run_once  # type: ignore
    cold = _run_once(story_id)
    warm = _run_once(story_id)
    return {"cold": cold, "warm": warm}


def load_baseline(story_id: int) -> dict:
    path = Path(f"docs/benchmarks/baselines/story-{story_id}.json")
    if not path.exists():
        return {"max_warm_seconds": 6.0, "min_warm_improvement_ratio": 0.80}
    return json.loads(path.read_text())


def enforce(b: dict, res: dict) -> int:
    cold = float(res["cold"]["duration_s"])
    warm = float(res["warm"]["duration_s"])
    max_warm = float(b.get("max_warm_seconds", 6.0))
    min_ratio = float(b.get("min_warm_improvement_ratio", 0.80))

    code = 0
    if warm > max_warm:
        print(f"FAIL: warm {warm:.3f}s exceeds budget {max_warm:.3f}s")
        code = 1
    elif cold > 0 and warm > cold * min_ratio:
        print(f"WARN: warm {warm:.3f}s not sufficiently faster than cold {cold:.3f}s (<= {min_ratio*100:.0f}% expected)")
    else:
        print("OK: within budgets")
    return code


def main() -> None:
    ap = argparse.ArgumentParser(description="Run benchmark and enforce baseline budgets")
    ap.add_argument("story_id", type=int)
    ap.add_argument("--json-out", type=str, default="bench.json")
    args = ap.parse_args()

    res = run_benchmark(args.story_id)
    Path(args.json_out).write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    code = enforce(load_baseline(args.story_id), res)
    sys.exit(code)


if __name__ == "__main__":
    main()

