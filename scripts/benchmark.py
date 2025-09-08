#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from pathlib import Path


def _clear_cache() -> None:
    d = Path('.a2dev/cache')
    if d.exists():
        shutil.rmtree(d)


def _run_once(story_id: int) -> dict:
    # Ensure lightweight mode to avoid external tool calls during bench
    os.environ.setdefault('A2DEV_MODE', 'off')
    # Choose orchestrator via factory
    from a2a.core import get_orchestrator
    orch = get_orchestrator()
    t0 = time.perf_counter()
    result = orch.prepare_story(story_id, also_scaffold=False)
    dt = time.perf_counter() - t0
    return {
        'duration_s': dt,
        'gate': bool(result.get('gate')),
        'created': len(result.get('artifacts', {}).get('created', [])),
        'existing': len(result.get('artifacts', {}).get('existing', [])),
        'agents': result.get('agents', []),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description='A2Dev benchmark harness (cold/warm cache)')
    ap.add_argument('story_id', type=int)
    ap.add_argument('--json', action='store_true', help='Print JSON results')
    ap.add_argument('--keep-cache', action='store_true', help='Do not clear cache first')
    args = ap.parse_args()

    if not args.keep_cache:
        _clear_cache()

    cold = _run_once(args.story_id)
    warm = _run_once(args.story_id)
    out = {'cold': cold, 'warm': warm}
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print('Benchmark results:')
        print(f"- Cold: {cold['duration_s']:.2f}s, gate={'PASS' if cold['gate'] else 'FAIL'}, created={cold['created']}")
        print(f"- Warm: {warm['duration_s']:.2f}s, gate={'PASS' if warm['gate'] else 'FAIL'}, created={warm['created']}")


if __name__ == '__main__':
    main()

