Agile ADDIE Dev Framework (A2Dev)

Overview
- Purpose: a lightweight agent‑to‑agent (A2A) scaffold where a PM role orchestrates planning and delivery. It favors tools with typed IO and repo‑persisted artifacts over opaque nested agents.
- Roles: PM coordinator (planning, routing), UX (flows/specs), Eng (scaffold/impl stubs). All outputs are stored under `docs/` and state under `.a2dev/`.

Quick Start
- Install into an existing project (optional): `python3 scripts/install_a2dev.py --dest .`
- Create or edit a PRD at `docs/PRD.md` (or use the sample at `docs/PRD_SAMPLE.md`).
- Plan backlog: `python3 a2dev_cli.py plan docs/PRD.md`
- Generate UX for story 1: `python3 a2dev_cli.py ux 1`
- Start building story 1: `python3 a2dev_cli.py start 1`
 - Architecture ADR: `python3 a2dev_cli.py arch 1`
 - Deep plan: `python3 a2dev_cli.py plan-deep 1`
 - QA plan: `python3 a2dev_cli.py qa-plan 1`
 - Threat model: `python3 a2dev_cli.py threat 1`
 - DevOps plan: `python3 a2dev_cli.py devops-plan 1`
 - Analytics spec: `python3 a2dev_cli.py data-plan 1`
 - Traceability: `python3 a2dev_cli.py trace 1`
 - Shard story: `python3 a2dev_cli.py shard 1`
 - Gate check: `python3 a2dev_cli.py gate 1`
 - One-shot prep: `python3 a2dev_cli.py prepare-story 1`

What You Get
- `docs/backlog.json` — epics/stories parsed from the PRD.
- `docs/epics.md` — human‑readable outline.
- `docs/ux/story-<id>.md` — UX document per story.
- `features/story-<id>/` — Eng scaffold for implementation (placeholder files).
- `.a2dev/state.json` — coordinator state and pointers.

Design Principles
- PM as coordinator: a single orchestrator plans, gates, and delegates.
- Tools over agents: each role is a tool with clear contracts and artifacts.
- Traceability: every decision/artifact is file‑based and reviewable.
- Idempotence: steps can be re‑run safely; the PM resumes from state.

Model Selection
- The scaffold includes `a2dev/models.py` and `a2dev/llm.py` to route tasks by task type. Edit `REGISTRY` and `select_model` as needed.
- Tier control: set `A2A_MODEL_TIER=high|medium|low` (falls back to `CODEX_MODEL_TIER`/`MODEL_TIER`). Example: `A2A_MODEL_TIER=medium python3 a2dev_cli.py sm-prepare 2`.
- By default, LLM calls are stubbed; wire real SDKs and keys to enable generation.

Extending With LLMs
- The scaffold intentionally avoids network/deps. To use an LLM, implement the `llm_summarize()` and `llm_backlog()` hooks in `a2a/llm.py` and set `OPENAI_API_KEY` (or your provider of choice). Keep role outputs in the same schemas.

Slash Commands (optional)
- If you use a router in your harness, map:
  - `/plan docs/PRD.md` → `python3 a2dev_cli.py plan docs/PRD.md`
  - `/ux <ids>` → `python3 a2dev_cli.py ux <ids>`
  - `/arch <id>` → `python3 a2dev_cli.py arch <id>`
  - `/plan-deep <id>` → `python3 a2dev_cli.py plan-deep <id>`
  - `/qa <id>` → `python3 a2dev_cli.py qa-plan <id>`
  - `/threat <id>` → `python3 a2dev_cli.py threat <id>`
  - `/devops <id>` → `python3 a2dev_cli.py devops-plan <id>`
  - `/data <id>` → `python3 a2dev_cli.py data-plan <id>`
  - `/trace <id>` → `python3 a2dev_cli.py trace <id>`
  - `/shard <id>` → `python3 a2dev_cli.py shard <id>`
  - `/gate <id>` → `python3 a2dev_cli.py gate <id>`
  - `/prepare <id>` → `python3 a2dev_cli.py prepare-story <id>`

Structure
- `.a2dev/` — state, policies, semgrep rules
- `a2a/` — code (schemas, PM, roles, CLI)
- `a2dev_cli.py` — primary CLI entry
- `docs/` — PRD, backlog, UX docs
- `features/` — code scaffold per story

Requirements
- Python 3.10+
- Recommended tools: `ripgrep` (`rg`), `universal-ctags` (`ctags`), `semgrep`, `gitleaks`.
- Optional env: `A2A_MODEL_TIER=high|medium|low` (Codex tier hint).

Installation
- Option A — Script (recommended for existing repos)
  - `python3 scripts/install_a2dev.py --dest /path/to/project`
  - Creates `.a2dev/` (policies, semgrep), copies `a2dev_cli.py`, PR template, and a sample `docs/PRD.md` if missing.
- Option B — Manual
  - Copy `.a2dev/`, `a2dev_cli.py`, `AGENTS.md`, and `docs/PRD_SAMPLE.md` into your repo.
  - Rename `docs/PRD_SAMPLE.md` → `docs/PRD.md` and customize.
- Bootstrap
  - `python3 a2dev_cli.py bootstrap` (checks tools and prints install hints).

Uninstallation (conservative)
- Dry run: `python3 a2dev_cli.py uninstall` (lists A2Dev files that would be removed)
- Remove: `python3 a2dev_cli.py uninstall --force`
- Note: This removes A2Dev scaffolding (e.g., `.a2dev/`, CLI shims, AGENTS.md, examples, tools). It does not remove your project docs or code under `docs/*` or `features/`.

NPX-like one-liners (Node/npm)
- Using npx from GitHub (public repo):
  - `npx -y -p github:<your-user>/agile-addie-dev-framework a2dev pm next`
  - Runs the Node wrapper which invokes A2Dev locally (prefers `a2dev.pyz` if present, falls back to `a2dev_cli.py`).
- Build a single-file runner (optional):
  - `npm run build:pyz` then `npx -y -p github:<your-user>/agile-addie-dev-framework a2dev pm next`
- Private repos: GitHub-based npx works best when the repo is public. For private usage, prefer pipx/uvx or install this repo locally and run the `a2dev` bin from the project root.

Using In Different Surfaces
- CLI
  - Assess: `python3 a2dev_cli.py route "@analyst assess docs/PRD.md"`
  - Develop (PM): `python3 a2dev_cli.py route "@pm develop 2"` or `python3 a2dev_cli.py pm next`
  - Sustain (sPM): `python3 a2dev_cli.py route "@spm sustain 2"`
  - Timeline: `python3 a2dev_cli.py timeline <assess|id>`
- IDE (Codex)
  - Ensure `a2dev_cli.py` is at repo root.
  - Optionally wire `tools/codex_router_example.py` as a preprocessor to route `@analyst/@pm/@dev/@spm` or `*develop` messages to `route`.
  - Interact with a single persona (Analyst/PM/sPM) — PM coordinates sub‑agents.
- Web (Codex)
  - Commit `.a2dev/`, `a2dev_cli.py`, `AGENTS.md` (and optionally the router).
  - Use the same conversational commands in chat, or run CLI commands in the terminal pane.

Codex Harness Example
- Tools mapping (TS): see `examples/codex-tools.ts`. Each tool shells into `a2dev_cli.py` and returns stdout.
- Minimal harness runner (TS): see `examples/harness.ts`.
  - One-off: `npx ts-node examples/harness.ts route '{"text":"@pm develop 2"}'`
  - Interactive: `npx ts-node examples/harness.ts` then type `@pm develop 2`
  - Adapt this to your Codex Web/IDE harness by registering the tools and routing messages beginning with `@analyst/@pm/@dev/@spm` or `*` to the `route` tool.

PM‑Driven Commands (minimal set)
- `pm next` — pick next story and prepare (UX→ADR→Plan→QA→Sec→DevOps→Data→Trace→Shard→Gate)
- `pm continue` — resume current story or pick next
- `pm story <id>` — prepare a specific story; add `--scaffold` to create code scaffolding
- `assess <PRD.md>` — Analyst creates brief + backlog and advances to Develop
- `sustain <id>` — sPM runs sustainment gate
- `timeline <assess|id>` — show timeline

Status & Journal
- A short status line prints after each action (phase, persona, agents used, docs created, refs, gate result).
- Human timeline: `docs/timeline/assess.md`, `docs/timeline/story-<id>.md`
- Structured journal: `.a2dev/journal/*.jsonl`

Security & Quality (local‑first)
- Gates:
  - Semgrep: rules in `.a2dev/semgrep/rules.yml`; results saved under `docs/security/semgrep/`; gate fails if high severity > 0.
  - Secrets: gitleaks results saved under `docs/security/secrets/`; gate fails on any finding.
- Policies: `.a2dev/policies/` (Coding Standards, Code Review, Secure Coding, DoR, DoD)
- PR template: `.github/pull_request_template.md` references the policies.

README Best Practices (for your projects)
- Title: clear, concise project name.
- One‑liner: what it does in one sentence and who it’s for.
- Badges (optional): version, license, Python/Node version, etc.
- Table of Contents (for long READMEs).
- Requirements: languages, runtimes, OS caveats.
- Installation: copy‑paste commands for CLI, IDE, and Web usage.
- Quick Start: 3–5 commands from zero to demo.
- Usage: common workflows and minimal command list.
- Configuration: env vars, config files, secrets handling.
- Development: repo structure, how to run tests/lint, local debugging.
- Security: data classification, threat model location, scanning tools.
- Troubleshooting: common errors and quick fixes.
- License & Credits: clear licensing and attribution.

Troubleshooting
- Missing tools reported by `bootstrap`: install via Homebrew (macOS) or apt/pipx (Linux) per hints.
- Gate fails “Acceptance criteria missing”: add ACs in `docs/PRD.md` (then `plan`) or directly in `docs/backlog.json`.
- Semgrep high findings: open `docs/security/semgrep/story-<id>.json` and adjust code/policies.
- Secrets findings: rotate and remove secrets; re‑scan.

Publish (npm) Checklist (optional)
- Update `package.json` name/scope if publishing to npm (e.g., `@your-scope/a2dev`).
- Remove `private: true` and choose a license.
- Build a portable runner: `npm run build:pyz` (optional).
- Publish: `npm publish` (consider `--access public` for scoped packages).
- After publishing:
  - `npx @your-scope/a2dev pm next` (public)
  - or `npm i -D @your-scope/a2dev` to use the postinstall initializer in consuming repos.

One-liner install (npx style)
- Current (from GitHub): `npx -y -p github:<your-user>/agile-addie-dev-framework a2dev install`
- After publishing to npm: `npx @your-scope/a2dev install`


Installation Guide (CLI, IDE, Web)
- CLI
  - Prereqs: Python 3.10+, optional tools: `ripgrep`, `ctags`, `semgrep`, `gitleaks`.
  - Install: `git clone <this repo>` then `python3 scripts/install_a2dev.py --dest /path/to/project`.
  - Use: in your project root run A2Dev commands, e.g., `python3 a2dev_cli.py route "@analyst assess docs/PRD.md"`.
- IDE (Codex)
  - Open your project in Codex IDE. Ensure `a2dev_cli.py` is at project root.
  - Optional preprocessor: use `tools/codex_router_example.py` to map messages starting with `@analyst/@pm/@dev/@spm` or `*develop` to `a2dev_cli.py route` and surface output.
  - Interact: `@analyst assess docs/PRD.md`, `@pm develop 2`, `@spm sustain 2`.
- Web (Codex)
  - Commit `.a2dev/`, `a2dev_cli.py`, and optionally `tools/codex_router_example.py`.
  - Configure your Codex Web project to run the router for chat messages or use the terminal.
  - Rely on status lines and `docs/*` artifacts as shared context.

Timeline Viewer
- Show assess timeline: `python3 a2dev_cli.py timeline assess`
- Show story timeline: `python3 a2dev_cli.py timeline <id>`

Security Gates
- Semgrep: rules under `.a2dev/semgrep/rules.yml`. Results: `docs/security/semgrep/story-<id>.json`. Gate fails if high severity > 0.
- Secrets: install `gitleaks`. Results: `docs/security/secrets/story-<id>.json`. Gate fails if any findings exist.

Proposals & Sprints Overview
- Proposals (PM planning aid):
  - Generate: `python3 a2dev_cli.py story-proposals gen --capacity 20 --sprints all`
  - Refine: `python3 a2dev_cli.py story-proposals refine --accept 2,3 --estimate 6=3.0 --priority 2=must --capacity 20 --sprints all`
  - Accept into backlog: `python3 a2dev_cli.py story-proposals accept [--accept 2,3]`
  - Outputs:
    - `docs/proposals/proposed-backlog.json` and `.md`
    - `docs/proposals/sprint-<n>.md` (one per sprint)
    - `docs/proposals/plan.md` (index of proposed sprints)
    - `docs/proposals/summary.md` (must/should/could counts and total points)
- PM Sprints (from current backlog):
  - Plan: `python3 a2dev_cli.py pm-sprints --capacity 20 --weeks 2`
  - Outputs:
    - `docs/sprints/sprint-<n>.md` and overall `docs/sprints/plan.md`
