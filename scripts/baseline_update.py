#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def run_benchmark(story_id: int) -> dict:
    sys.path.insert(0, str(Path.cwd()))
    os.environ.setdefault("A2DEV_MODE", os.environ.get("A2DEV_MODE", "off"))
    from scripts.benchmark import _run_once  # type: ignore
    cold = _run_once(story_id)
    warm = _run_once(story_id)
    return {"cold": cold, "warm": warm}


def write_baseline(story_id: int, warm_seconds: float, ratio: float) -> str:
    baseline = {
        "max_warm_seconds": round(warm_seconds * 1.25, 3),
        "min_warm_improvement_ratio": max(0.70, min(0.95, round(ratio * 0.95, 2))),
        "notes": "Auto-updated baseline; review and adjust if needed."
    }
    out = Path(f"docs/benchmarks/baselines/story-{story_id}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(baseline, indent=2))
    return str(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="Run benchmark and update baseline file")
    ap.add_argument("story_id", type=int)
    ap.add_argument("--mode", choices=["on", "off"], default="off", help="A2Dev mode for run")
    args = ap.parse_args()

    os.environ["A2DEV_MODE"] = args.mode
    res = run_benchmark(args.story_id)
    cold = float(res["cold"]["duration_s"])
    warm = float(res["warm"]["duration_s"])
    ratio = warm / cold if cold > 0 else 0.0
    path = write_baseline(args.story_id, warm, ratio)
    print(json.dumps(res, indent=2))
    print(f"Baseline updated: {path}")


if __name__ == "__main__":
    main()

