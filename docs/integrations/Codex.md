# Codex Integration Guide (Route Tool + Roles)

This project is designed to be driven entirely from Codex via tools. The only tool you must expose is `route` — it handles `@analyst/@pm/@spm/@dev` and `*commands` and coordinates everything else.

## 1) Register the `route` tool

Minimal schema (function/tool):

```
name: route
description: Conversational router for @role and *commands
parameters:
  type: object
  properties:
    text:
      type: string
  required: [text]
run: python3 a2dev_cli.py route "{{text}}"
```

Optionally also expose: `pm_next`, `pm_story`, `assess`, `develop`, `sustain`, `gate_check`, `timeline`, `pm_sprints`. The router is sufficient for most workflows.

## 2) System prompt (routing policy)

Paste into your system message so Codex reliably calls the tool:

```
You are the A2Dev PM/Analyst/sPM assistant. Tools are available. Routing policy:
- If a user message starts with @analyst/@pm/@spm/@dev or with *, ALWAYS call the route tool with the full text unchanged.
- If the message is not prefixed and an active role exists in .a2dev/state.json, prepend @<active_role> and call route.
- If no active role exists, call route with "@analyst" to begin assessment.
Keep responses concise, include next‑step options, and never simulate tool behavior.
```

## 3) Role flow and persistence

- `@analyst` with no args prints assessment choices and sets the active role to Analyst.
- `@analyst assess fresh|prepared <path>|codebase` runs the chosen assessment flow.
- After assessment, the CLI prints a “Handoff to Codex” with the next chat command (e.g., `@pm develop <id>`).
- The active role is stored in `.a2dev/state.json` (`active_role`). Your router can forward un‑prefixed messages to this role. Route messages by calling `python3 a2dev_cli.py route "<message>"`.

## 4) Example harness (outline)

Register the `route` tool and forward `@analyst/@pm/@spm/@dev` or `*command` messages to `python3 a2dev_cli.py route "<message>"`. Optionally, mirror the other tools (`pm_next`, `pm_story`, `assess`, `develop`, `sustain`, `gate_check`, `timeline`, `pm_sprints`).

## 5) Troubleshooting

- Typing `@analyst` does nothing: ensure the `route` tool is registered and your system prompt instructs calling it on @-prefixed messages.
- Bare messages aren’t routed: ensure your router checks `.a2dev/state.json` and forwards to the active role.
- First‑time install errors: run `python3 a2dev_cli.py install --dest .` in the project; then `python3 a2dev_cli.py quickstart` if you want the interactive menu.
