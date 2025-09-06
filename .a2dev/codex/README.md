# Codex Integration (A2Dev)

This project is preconfigured for Codex (CLI/Web). Import these once, then just chat with `@analyst`, `@pm`, `@spm`.

## System Prompt
Use: `.a2dev/codex/system-prompt.txt` as your system message.

## Tools
Prefer Node tools: `.a2dev/codex/tools.node.json` (runs `node node_modules/a2dev/bin/a2dev.js ...`).

Alternative Python tools: `.a2dev/codex/tools.python.json` (runs `python3 a2dev_cli.py ...`).

Required tool: `route` — forward any message starting with `@analyst/@pm/@spm/@dev` or `*` to this tool with the full text.

## Behavior
- The router persists the active role in `.a2dev/state.json`.
- Unprefixed messages should be forwarded to `@<active_role>` via the route tool.
- After setup, users simply type `@analyst` to get the greeting and options.
