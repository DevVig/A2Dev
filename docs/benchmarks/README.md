# Benchmarks

## Local
- Mode off (reproducible):
  - `PYTHONPATH=$PWD python3 scripts/benchmark.py <story_id> --json`
- Mode on (includes scans if enabled):
  - `PYTHONPATH=$PWD A2DEV_MODE=on python3 scripts/benchmark.py <story_id> --json`

## CI
- Workflow `.github/workflows/perf-bench.yml` runs a matrix over stories (1, 2).
- Uses `scripts/bench_ci.py` to run and enforce budgets against baselines.

## Baselines
- Files in `docs/benchmarks/baselines/story-<id>.json` with fields:
  - `max_warm_seconds`
  - `min_warm_improvement_ratio`
- Update baseline from current measurements:
  - `PYTHONPATH=$PWD python3 scripts/baseline_update.py <story_id> --mode off`

