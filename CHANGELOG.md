# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project adheres to Semantic Versioning.

## [0.1.0] - 2025-09-04
### Added
- Node wrapper (`a2dev`) with `.env.local` auto-loading.
- Postinstall initializer and `.env.example` copy.
- PM pipeline commands and gate criteria documented.
- CI workflow (smoke) and release workflow (npm publish + attach `a2dev.pyz`).
- Pre-commit hook sample for gitleaks and semgrep under `.a2dev/hooks/`.

## [0.1.1] - 2025-09-04
### Added
- `a2dev doctor` command for environment + project readiness checks.
- Simplified interactive setup menu with 3 primary paths (Start Fresh, I come prepared, I already started).
- `quickstart` alias for `setup` to open the menu quickly.

### Improved
- Brownfield assessment flow now includes a code quality audit by default.
- Audit writes hotspot analysis (by file count and total bytes).
- Installer bootstrap uses packaged CLI to avoid first-run `ModuleNotFoundError`.

### Changed
- README Quick Start favors `npx a2dev` usage.
- Story 1 sample ACs to pass gate on first run.

### Security
- `.gitignore` ignores `.env*` files by default.
