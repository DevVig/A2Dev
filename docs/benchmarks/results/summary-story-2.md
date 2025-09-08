# Benchmark Summary — Story 2

Latest run: 2025-09-07T23:59:33Z
Result file: docs/benchmarks/results/story-2-20250907T235933Z.json

Cold: 0.014s, gate=FAIL, created=0, existing=17
Warm: 0.010s, gate=FAIL, created=0, existing=17

Budgets
- Warm < 6.0s: PASS
- Warm <= 80% of cold: PASS (68.3%)

Notes
- Fast times reflect cached/ready artifacts and mode-off static scans during bench.
- Use perf.yaml to tune worker count and rate if tasks expand.

