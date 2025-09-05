#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path
root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

def _ensure_a2a_on_path() -> None:
    try:
        import a2a  # type: ignore
        return
    except Exception:
        pass
    hint = os.getenv("A2DEV_PY_PKG_PATH")
    if hint:
        p = Path(hint)
        if (p / "a2a").exists():
            sys.path.insert(0, str(p))
            try:
                import a2a  # type: ignore
                return
            except Exception:
                pass
    def _try_node_modules(base: Path) -> bool:
        nm = base / "node_modules"
        if not nm.is_dir():
            return False
        candidates = [nm / "a2dev"]
        try:
            for scope in nm.glob("@*/a2dev"):
                candidates.append(scope)
        except Exception:
            pass
        for pkg_root in candidates:
            if (pkg_root / "a2a" / "cli.py").exists():
                sys.path.insert(0, str(pkg_root))
                try:
                    import a2a  # type: ignore
                    return True
                except Exception:
                    pass
        return False
    tried: set[str] = set()
    for start in {Path.cwd(), root}:
        for parent in [start] + list(start.parents):
            key = str(parent)
            if key in tried:
                continue
            tried.add(key)
            if _try_node_modules(parent):
                return
    # Fall back to pyz
    for pyz in (Path.cwd() / "a2dev.pyz", root / "a2dev.pyz"):
        if pyz.exists():
            py = os.environ.get("PYTHON", sys.executable or "python3")
            os.execv(py, [py, str(pyz), *sys.argv[1:]])
    sys.stderr.write(
        "A2Dev: could not locate Python package 'a2a'.\n"
        "- If installed via npm: ensure node_modules contains 'a2dev'.\n"
        "- Or set A2DEV_PY_PKG_PATH to the package root containing 'a2a/'.\n"
        "- Or run via Node: npx a2dev <cmd>.\n"
    )
    sys.exit(1)

def _load_env_local():
    candidates = [Path.cwd() / ".env.local", root / ".env.local"]
    for p in candidates:
        try:
            if not p.exists():
                continue
            for raw in p.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                os.environ.setdefault(k, v)
        except Exception:
            pass

_load_env_local()
_ensure_a2a_on_path()

from a2a.cli import main as _main

# Temporary shim to maintain compatibility after rename to A2Dev
def main():
    _main()

if __name__ == "__main__":
    main()
