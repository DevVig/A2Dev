# Security Policy

Reporting a Vulnerability
- Please open a private security advisory on GitHub or email the maintainers.
- Do not create public issues for vulnerabilities or share exploit details publicly.

Secrets Handling
- Never commit real secrets. Use `.env.local` for local development and `.env.example` as a template.
- Pre-commit sample hook is available at `.a2dev/hooks/pre-commit.sample` (gitleaks + semgrep).

Scanning
- Recommended local checks before PRs:
  - `gitleaks detect --no-git --report-format json`
  - `semgrep --config auto`

Support
- For questions about security posture or gates, open a discussion or contact maintainers.

