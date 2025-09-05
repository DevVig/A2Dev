#!/usr/bin/env python3
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# Make the CLI robust when copied into a consumer repo without the local `a2a` package.
# If `import a2a` fails, search common Node install paths (node_modules/a2dev or @*/a2dev)
# and add the package root to sys.path. As a last resort, try running a bundled a2dev.pyz.
def _ensure_a2a_on_path() -> None:
    try:
        import a2a  # type: ignore
        return
    except Exception:
        pass
    # Allow explicit override
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
    # Search upwards for node_modules and known package names
    def _try_node_modules(base: Path) -> bool:
        nm = base / "node_modules"
        if not nm.is_dir():
            return False
        candidates = [nm / "a2dev"]
        # Scoped packages (e.g., @your-scope/a2dev)
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
                    # keep searching
                    pass
        return False

    # Try from CWD upwards and from this file's dir upwards
    tried: set[str] = set()
    for start in {Path.cwd(), root}:
        for parent in [start] + list(start.parents):
            key = str(parent)
            if key in tried:
                continue
            tried.add(key)
            if _try_node_modules(parent):
                return

    # Final fallback: try to exec a local or packaged a2dev.pyz
    pyz_candidates = [
        Path.cwd() / "a2dev.pyz",
        root / "a2dev.pyz",
    ]
    for pyz in pyz_candidates:
        if pyz.exists():
            # Re-exec into the pyz with same args
            py = os.environ.get("PYTHON", sys.executable or "python3")
            os.execv(py, [py, str(pyz), *sys.argv[1:]])
    # If we get here, a2a isn’t importable
    sys.stderr.write(
        "A2Dev: could not locate Python package 'a2a'.\n"
        "- If installed via npm: ensure node_modules contains 'a2dev' and rerun.\n"
        "- Or set A2DEV_PY_PKG_PATH to the package root containing 'a2a/'.\n"
        "- Or run via Node: npx a2dev <cmd> (preferred).\n"
    )
    sys.exit(1)

def _load_env_local():
    """Load key=value pairs from .env.local into os.environ if not already set.
    Avoids external dependencies (python-dotenv).
    """
    candidates = [Path.cwd() / ".env.local", Path(__file__).resolve().parent / ".env.local"]
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
            # Non-fatal; continue without env file
            pass

_load_env_local()
_ensure_a2a_on_path()

from a2a.cli import main

if __name__ == "__main__":
    main()
