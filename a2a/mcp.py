from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


def _run(cmd: List[str], cwd: Optional[str] = None, timeout: int = 120) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as e:
        return 1, "", str(e)


@dataclass
class CodeSearchResult:
    path: str
    line: int
    snippet: str


class CodeSearchAdapter:
    def search(self, query: str, root: str = ".") -> List[CodeSearchResult]:
        if shutil.which("rg"):
            code, out, _ = _run(["rg", "-n", "--no-heading", query], cwd=root)
        else:
            code, out, _ = _run(["grep", "-R", "-n", query, "."], cwd=root)
        results: List[CodeSearchResult] = []
        if code != 0:
            return results
        for line in out.splitlines():
            try:
                path, lno, text = line.split(":", 2)
                results.append(CodeSearchResult(path=path, line=int(lno), snippet=text.strip()))
            except Exception:
                continue
        return results


class SemgrepAdapter:
    def scan(self, root: str = ".", config: str = "auto") -> Dict[str, Any]:
        if not shutil.which("semgrep"):
            return {"status": "skipped", "reason": "semgrep not installed"}
        code, out, err = _run(["semgrep", "--config", config, "--json", root])
        if code != 0:
            return {"status": "error", "stderr": err}
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return {"status": "error", "stderr": "invalid json"}


class SupabaseAdapter:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self._client = None
        try:
            from supabase import create_client  # type: ignore

            if self.url and self.key:
                self._client = create_client(self.url, self.key)
        except Exception:
            self._client = None

    def status(self) -> str:
        if self._client:
            return "ready"
        return "not_configured"

    # Add domain-specific helpers as needed


class RefAdapter:
    """Lightweight code reference adapter (stand-in for code graph/ref tools)."""

    def index_exists(self, root: str = ".") -> bool:
        return Path(root, ".tags").exists()

    def build_index(self, root: str = ".") -> str:
        # Try universal-ctags if available
        if not shutil.which("ctags"):
            return "ctags not installed; skipped"
        code, out, err = _run(["ctags", "-R"], cwd=root)
        if code == 0:
            return "built"
        return f"error: {err}"


class GitleaksAdapter:
    """Secrets scanning via gitleaks CLI if available."""

    def scan(self, root: str = ".") -> Dict[str, Any]:
        if not shutil.which("gitleaks"):
            return {"status": "skipped", "reason": "gitleaks not installed"}
        code, out, err = _run(["gitleaks", "detect", "--no-git", "--report-format", "json", "--source", root])
        if code not in (0, 1):  # gitleaks returns 1 when leaks found
            return {"status": "error", "stderr": err}
        try:
            data = json.loads(out.strip() or "{}")
        except Exception:
            return {"status": "error", "stderr": "invalid json"}
        # Normalize
        findings = data if isinstance(data, list) else data.get("findings", [])
        return {"status": "ok", "findings": findings}
