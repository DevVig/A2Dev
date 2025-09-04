#!/usr/bin/env bash
set -euo pipefail

echo "[A2Dev] Startup begin"

# Move to repo root (script may be called from anywhere)
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="${SCRIPT_DIR%/scripts}"
cd "$ROOT_DIR"

PY="${PYTHON:-python3}"

echo "[A2Dev] Running bootstrap checks"
$PY a2dev_cli.py bootstrap || true

echo "[A2Dev] Ensuring code reference index (ctags)"
if command -v ctags >/dev/null 2>&1; then
  if [ ! -f "$ROOT_DIR/.tags" ]; then
    ctags -R || true
  fi
else
  echo "[A2Dev] ctags not found (optional)"
fi

echo "[A2Dev] Building portable runner (a2dev.pyz)"
$PY scripts/build_pyz.py || true

echo "[A2Dev] Suggested alias: add to your shell profile"
echo "  alias a2dev=\"$PY $ROOT_DIR/a2dev_cli.py\""

echo "[A2Dev] Quick commands:"
echo "  a2dev route \"@analyst assess docs/PRD.md\""
echo "  a2dev pm next"
echo "  a2dev timeline assess"

echo "[A2Dev] Startup complete"

