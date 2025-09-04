---
name: Publish Checklist
about: Steps to prepare and publish a new release
title: 'Release vX.Y.Z'
labels: release
assignees: ''
---

## Pre-release
- [ ] Update CHANGELOG.md with version and notes
- [ ] Update README if needed
- [ ] Bump version in package.json
- [ ] Run `python3 a2dev_cli.py smoke`
- [ ] Run `a2dev bootstrap` (or `python3 a2dev_cli.py bootstrap`)
- [ ] Local scans pass (optional): `gitleaks detect --no-git`, `semgrep --config auto`

## Tag and publish
- [ ] Create and push tag `vX.Y.Z`
- [ ] Confirm GitHub Actions CI passes
- [ ] Confirm npm publish succeeded (requires NPM_TOKEN in repo secrets)
- [ ] Confirm GitHub Release has `a2dev.pyz` attached

## Post-release
- [ ] Smoke test `npx a2dev install` in a fresh project
- [ ] Open follow-up issues for any docs or bugs discovered

