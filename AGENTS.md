## A2Dev Agents and Tools (Codex-Ready)

Overview
- Interaction model: single contact per phase.
  - Assess: talk to `@analyst`.
  - Develop: talk to `@pm` (PM coordinates sub‑agents automatically).
  - Sustain: talk to `@spm`.
  - Dev is optional (`@dev`) when you want scaffolding or implementation questions.
- Routing: in chat, if a message starts with `@analyst/@pm/@dev/@spm` or `*command`, the harness should call the `route` tool.
- Active role: after invoking a role, the router persists that role in `.a2dev/state.json` (`active_role`). Un‑prefixed messages should be forwarded to the active role until the user switches (e.g., `@pm …`) or issues `@<role> exit`.
- Status: after each action, print one short status line. Persist journal entries and a human timeline under `docs/timeline/`.

Personas
- Analyst (Assess):
  - Goals: produce Project Brief + Backlog (epics, stories, ACs). Prepare for Develop.
  - Triggers:
    - `@analyst` → show options: Fresh | Prepared | Codebase
    - `@analyst assess fresh` (create PRD + assess)
    - `@analyst assess prepared docs/PRD.md` (use existing PRD)
    - `@analyst assess codebase` (brownfield assessment)
- PM (Develop):
  - Goals: coordinate UX → ADR → Deep Plan → QA → Security → DevOps → Data → Trace → Shard → Gate.
  - Triggers:
    - `@pm develop <story_id>` or `*develop <story_id>`
    - `@pm next` / `@pm continue` (auto-select next or current story)
    - `@pm scaffold <story_id|next>` (prepare with scaffolding)
- sPM (Sustain):
  - Goals: confirm gates, security findings, rollout plan, monitoring readiness.
  - Triggers:
    - `@spm sustain <story_id>`
    - `@spm stabilize` (generate a maintenance plan from the latest audit)
- Dev (optional):
  - Goals: scaffold code; start implementation under `features/story-<id>/`.
  - Trigger: `@dev develop <story_id>`

Role Deliverables & Emphasis
- UI/UX (sub‑tool)
  - PM phase: UX story spec (`docs/ux/story-<id>.md`), Front‑End Spec, A11y Checklist (`docs/ux/a11y/story-<id>.md`).
  - sPM phase: A11y fixes, small usability improvements, component consistency.
- Architecture (sub‑tool)
  - PM phase: ADR (`docs/architecture/ADR-story-<id>.md`), Architecture Doc.
  - High‑risk: Architecture Review (`docs/architecture/reviews/story-<id>.md`).
- DevOps (sub‑tool)
  - PM phase: DevOps Plan (`docs/devops/story-<id>.md`).
  - High‑risk/sPM: Runbook (`docs/devops/runbooks/story-<id>.md`), SLOs/alerts.

Codex Tools (suggested)
- route(text: string)
  - Description: conversational router for `@role` and `*command` messages.
  - Example: `@pm develop 2`, `@analyst assess docs/PRD.md`, `*develop 3`.
- pm_next(scaffold?: boolean)
  - Description: PM picks the next story and prepares it (run pipeline + gate).
- pm_continue(scaffold?: boolean)
  - Description: PM continues the current story; if none, picks next.
- pm_story(id: number, scaffold?: boolean)
  - Description: PM prepares a specific story id.
- assess(prd_path: string)
  - Description: Analyst produces brief + backlog; advances phase.
- develop(story_id: number)
  - Description: PM runs full develop pipeline for a story.
- sustain(story_id: number)
  - Description: sPM runs sustainment gate.
- gate_check(story_id: number)
  - Description: check gates for a story; returns issues.
- timeline(target: "assess" | number)
  - Description: show assess or story timeline.
- pm_sprints(capacity?: number, weeks?: number)
  - Description: plan sprints from the backlog.

Tool → CLI mapping
- route → `python3 a2dev_cli.py route "<text>"`
- pm_next → `python3 a2dev_cli.py pm next [--scaffold]`
- pm_continue → `python3 a2dev_cli.py pm continue [--scaffold]`
- pm_story → `python3 a2dev_cli.py pm story <id> [--scaffold]`
- assess → `python3 a2dev_cli.py assess <prd_path>`
- develop → `python3 a2dev_cli.py develop <story_id>`
- sustain → `python3 a2dev_cli.py sustain <story_id>`
- gate_check → `python3 a2dev_cli.py gate <story_id>`
- timeline → `python3 a2dev_cli.py timeline <assess|id>`
- pm_sprints → `python3 a2dev_cli.py pm-sprints [--capacity N] [--weeks N]`

Operating Guidance (system prompt excerpt)
- You are the A2Dev PM/Analyst/sPM. ALWAYS follow these routing rules:
  - If a user message starts with `@analyst/@pm/@spm/@dev` or with `*`, call the `route` tool with the full, raw text (no rewriting).
  - If a message does not start with `@` or `*` and an active role exists in `.a2dev/state.json`, prepend `@<active_role>` and call `route`.
  - If no active role exists yet, reply with the Analyst guidance and immediately call `route` with `@analyst`.
  - Provide succinct next‑step choices after each action (e.g., role‑specific numbered options or `@<role> help`).
  - Do not attempt to simulate role actions; always call tools.
  
Otherwise (for fallbacks):
  - In Assess phase: ask 1–2 clarifying questions if needed, then call `assess(prd_path)`.
  - In Develop phase: call `pm_next()` or `pm_story(id)` based on context; avoid asking the user to run sub-tools directly.
  - In Sustain phase: call `sustain(story_id)` or `gate_check(story_id)`.
- Always print one short status line after each action.
- Persist artifacts under `docs/*` and update the timeline.
- Best practices:
  - UI/UX: WCAG 2.1 AA, design tokens, component‑driven, heuristic review, a11y testing.
  - Architecture: ADRs, C4 maps, 12‑factor/NFRs, evolutionary change, API contracts.
  - DevOps: DORA metrics, CI/CD gates, IaC, GitOps/trunk, SLO/SLI, runbooks, feature flags.

Bootstrap (startup script suggestion)
- Run `python3 a2dev_cli.py bootstrap` on startup to check tools (rg, ctags, semgrep, gitleaks) and give install hints.
- Build code ref index: run ctags if missing.

Codex Tools (JSON schema examples)
- Define these tools in your Codex harness; each tool shells into the CLI. Return both stdout and a structured JSON where possible.

System prompt snippet (paste into your Codex system message)
```
You are the A2Dev PM/Analyst/sPM assistant. Tools are available. Routing policy:
- If a user message starts with @analyst/@pm/@spm/@dev or with *, ALWAYS call the route tool with the full text unchanged.
- If the message is not prefixed and an active role exists in .a2dev/state.json, prepend @<active_role> and call route.
- If no active role exists, call route with "@analyst" to begin assessment.
Keep responses concise, include next‑step options, and never simulate tool behavior.
```

1) route
{
  "name": "route",
  "description": "Conversational router for @role and *commands",
  "parameters": {
    "type": "object",
    "properties": { "text": { "type": "string" } },
    "required": ["text"]
  },
  "run": "python3 a2dev_cli.py route \"{{text}}\""
}

JSON output (optional)
- Set `A2DEV_OUTPUT=json` in the tool environment to receive structured JSON events from `route` instead of plain text. This is useful for rendering menus, cards, or state in your UI.
- Each JSON event may include a `suggestions` array with `{label, command}` items you can surface as buttons or quick replies.

2) pm_next
{
  "name": "pm_next",
  "description": "PM picks the next story and prepares it",
  "parameters": {
    "type": "object",
    "properties": { "scaffold": { "type": "boolean", "default": false } }
  },
  "run": "python3 a2dev_cli.py pm next {{#if scaffold}}--scaffold{{/if}}"
}

3) pm_continue
{
  "name": "pm_continue",
  "description": "PM continues the current story or picks next",
  "parameters": {
    "type": "object",
    "properties": { "scaffold": { "type": "boolean", "default": false } }
  },
  "run": "python3 a2dev_cli.py pm continue {{#if scaffold}}--scaffold{{/if}}"
}

4) pm_story
{
  "name": "pm_story",
  "description": "PM prepares a specific story id",
  "parameters": {
    "type": "object",
    "properties": { "id": { "type": "integer" }, "scaffold": { "type": "boolean", "default": false } },
    "required": ["id"]
  },
  "run": "python3 a2dev_cli.py pm story {{id}} {{#if scaffold}}--scaffold{{/if}}"
}

5) assess
{
  "name": "assess",
  "description": "Analyst produces brief + backlog; advances phase",
  "parameters": {
    "type": "object",
    "properties": { "prd_path": { "type": "string" } },
    "required": ["prd_path"]
  },
  "run": "python3 a2dev_cli.py assess {{prd_path}}"
}

6) develop
{
  "name": "develop",
  "description": "PM runs full develop pipeline for a story",
  "parameters": {
    "type": "object",
    "properties": { "story_id": { "type": "integer" } },
    "required": ["story_id"]
  },
  "run": "python3 a2dev_cli.py develop {{story_id}}"
}

7) sustain
{
  "name": "sustain",
  "description": "sPM runs sustainment gate",
  "parameters": {
    "type": "object",
    "properties": { "story_id": { "type": "integer" } },
    "required": ["story_id"]
  },
  "run": "python3 a2dev_cli.py sustain {{story_id}}"
}

8) gate_check
{
  "name": "gate_check",
  "description": "Check gates and return issues",
  "parameters": {
    "type": "object",
    "properties": { "story_id": { "type": "integer" } },
    "required": ["story_id"]
  },
  "run": "python3 a2dev_cli.py gate {{story_id}}"
}

9) timeline
{
  "name": "timeline",
  "description": "Show assess or story timeline",
  "parameters": {
    "type": "object",
    "properties": { "target": { "type": "string" } },
    "required": ["target"]
  },
  "run": "python3 a2dev_cli.py timeline {{target}}"
}

10) pm_sprints
{
  "name": "pm_sprints",
  "description": "Plan sprints from the backlog",
  "parameters": {
    "type": "object",
    "properties": { "capacity": { "type": "number", "default": 20 }, "weeks": { "type": "integer", "default": 2 } }
  },
  "run": "python3 a2dev_cli.py pm-sprints --capacity {{capacity}} --weeks {{weeks}}"
}
