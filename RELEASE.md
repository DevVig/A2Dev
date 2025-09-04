Release Checklist (npm)

1) Choose package name & scope
- Recommended: scoped name, e.g., `@your-scope/a2dev`.
- Update `package.json` fields:
  - `name`: "@your-scope/a2dev"
  - Remove `"private": true`
  - `repository.url`: your Git HTTPS URL
  - `homepage`: your repo page
  - `license`: pick one (MIT/Apache-2.0/UNLICENSED etc.)

2) Verify published contents
- `files` array in `package.json` limits contents to:
  - `bin/`, `a2a/**`, `a2dev_cli.py`, `a2a_cli.py`, `AGENTS.md`, `README_A2Dev.md`, `.a2dev/**`, `docs/PRD_SAMPLE.md`, `scripts/*`, `tools/codex_router_example.py`, `examples/*`
- Adjust if you want to exclude examples.

3) Build portable runner (optional)
- `npm run build:pyz` to create `a2dev.pyz` (not included by default; you can add it to `files` if desired).

4) Dry run
- `npm pack --dry-run` to inspect contents.

5) Publish
- Remove `private: true`.
- `npm publish --access public` (for scoped packages).

6) Verify install paths
- Fresh project: `npx @your-scope/a2dev install`
- Confirm it initializes `.a2dev/`, `docs/PRD.md`, CLI shims, and runs bootstrap.

7) Tag and changelog
- Tag `vX.Y.Z` and update CHANGELOG if you maintain one.

