# CLI RFC — Mode and Performance Flags

Goals: Introduce discoverable flags to control A2Dev mode, intelligence, parallelism, and caching without breaking existing behavior.

## Flags
- `--mode on|off` (env: `A2DEV_MODE`)
- `--intelligence on|off` (project default in `.a2dev/intelligence.yaml`)
- `--parallel on|off|auto` (default: auto)
- `--cache on|off` (default: on)

## Behavior
- No flags: use project defaults. Flags override env; env overrides config.
- OFF mode disables optional analysis (e.g., Semgrep/Gitleaks) and runs minimal path when available.

## Help/Docs
- Update CLI help and README with flag descriptions and examples.

