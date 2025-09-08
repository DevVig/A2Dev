# Benchmark Harness and Methodology

Date: 2025-09-07

## Goals
- Establish reproducible baselines and enforce performance budgets in CI.

## Scenarios
- Cold cache: first run after cache clear.
- Warm cache: repeat run with unchanged inputs.

## Dataset
- Fixed PRD/backlog and 3 sample stories (small/medium/large).
- Seeded prompts and deterministic parameters.

## Metrics
- Latency p50/p90 per artifact; total pipeline time.
- Cache: hit/miss/eviction counts.
- Resource: memory (RSS) and CPU time.

## Execution
1. Cold run (clears cache): `scripts/benchmark.py <story_id> --json`
2. Warm run (auto second pass): same command outputs both.
3. Compare against baselines with tolerance bands in CI.

Notes
- The harness sets `A2DEV_MODE=off` to avoid external tool calls during measurements.

## CI Budget
- Fail if latency regressions exceed 20% for two consecutive runs.
- Export JSON results for dashboards.
