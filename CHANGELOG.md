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

### Changed
- README Quick Start favors `npx a2dev` usage.
- Story 1 sample ACs to pass gate on first run.

### Security
- `.gitignore` ignores `.env*` files by default.

