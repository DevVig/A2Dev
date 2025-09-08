# A2Dev Mode Switch

Purpose: Quickly toggle project behavior between A2Dev mode and a minimal/vanilla mode.

## Options
- Config file: `.a2dev/mode.yaml` with `a2dev_mode: on|off`.
- Env var override: `A2DEV_MODE=on|off` (if supported by runtime; safe to add).
- Intelligence layer: independent toggle via `.a2dev/intelligence.yaml: enabled`.
- Quick toggle (unified chat/CLI): type `@a2D` (or `A2D`) to flip ON/OFF.
  - CLI: `a2dev route "@a2D"`
  - Chat/Web: send `@a2D` in the router-enabled chat

## Guidance
- Keep `a2dev_mode: on` for normal operation. Set `off` for minimal runs without A2Dev guidance.
- When OFF:
  - The `route` command is disabled (no auto-greetings, no persona menus).
  - Optional static analysis (Semgrep/Gitleaks) is skipped in orchestrator.
  - You can still run direct CLI commands (e.g., `a2dev develop <id>`), or interact with Codex directly without A2Dev prompts.
- Gates remain invariant; artifacts are still generated when you call commands explicitly.

## CLI
- Show mode: `a2dev mode status`
- Set mode: `a2dev mode set on|off`
- Toggle: `a2dev mode toggle`
