# Contributing to A2Dev

Thanks for your interest! A2Dev aims to provide a lightweight, PM‑led orchestration layer developers can use locally.

How to contribute
- Issues: search existing issues; include repro steps and environment info.
- Pull Requests: fork, create a feature branch, keep changes focused. Link to an issue when possible.
- Style: keep changes minimal and dependency‑light; prefer standard library; no network calls by default.
- Commits: use Conventional Commits (feat:, fix:, docs:, chore:, ci:, refactor:, test:).
- Tests: add smoke or targeted tests where applicable; don’t add heavy frameworks.

Development setup
- Python 3.10+, Node 18+.
- Optional tools: ripgrep, universal-ctags, semgrep, gitleaks.
- Quick dev loop: `python3 a2dev_cli.py smoke` and `npm run build:pyz`.

Release process
- Update CHANGELOG.md.
- Bump version in `package.json`.
- Tag with `vX.Y.Z` and push; CI will publish to npm and attach `a2dev.pyz` to the GitHub release.

Code of Conduct
- Be respectful and constructive. We aim for a welcoming, collaborative community.
