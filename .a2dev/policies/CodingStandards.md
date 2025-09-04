Coding Standards (Language-Agnostic)

- Simplicity: prefer clear, small functions; avoid cleverness.
- Cohesion: one responsibility per module/class/function.
- Coupling: keep dependencies narrow; inject where feasible.
- Naming: descriptive names; avoid abbreviations; align with domain terms.
- Errors: fail fast with explicit exceptions; avoid silent failures.
- Logging: structured logs at boundaries; no secrets in logs.
- Tests: write unit tests for new logic; cover edge cases.
- Docs: docstrings or comments for non-obvious behavior; keep READMEs updated.
- Config: use env vars; never hardcode secrets; support local overrides.
- Performance: measure before optimizing; add basic benchmarks if critical.

