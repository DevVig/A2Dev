from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import os

from ..storage import read_state


def project_root() -> Path:
    return Path.cwd()


def read_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
        if path.exists():
            return yaml.safe_load(path.read_text()) or {}
    except Exception:
        pass
    return {}


def get_mode_flags() -> Dict[str, Any]:
    root = project_root()
    mode = read_yaml(root / ".a2dev" / "mode.yaml")
    intel = read_yaml(root / ".a2dev" / "intelligence.yaml")
    # Env overrides
    import os
    env_mode = os.getenv("A2DEV_MODE")
    if env_mode:
        mode["a2dev_mode"] = env_mode
    return {
        "a2dev_mode": mode.get("a2dev_mode", "on"),
        "intelligence_enabled": bool(intel.get("enabled", False)),
        "intelligence": intel,
    }


def get_perf_flags() -> Dict[str, Any]:
    cfg = read_yaml(project_root() / ".a2dev" / "perf.yaml")
    env_par = (os.getenv("A2DEV_PARALLEL") or "").lower()
    env_cache = (os.getenv("A2DEV_CACHE") or "").lower()
    env_rps = os.getenv("A2DEV_RPS")
    par = env_par or str(cfg.get("parallel", "auto")).lower()
    cache = env_cache or str(cfg.get("cache", "on")).lower()
    ttl = int(cfg.get("ttl_minutes", 60))
    maxw = int(cfg.get("max_workers", 0) or 0)
    # Auto-size workers if requested
    if (par in {"on", "auto"}) and (not maxw or maxw <= 0):
        try:
            import os as _os
            cpu = max(1, _os.cpu_count() or 2)
            maxw = max(2, min(8, cpu * 2))
        except Exception:
            maxw = 4
    rps = float(env_rps) if (env_rps and env_rps.replace('.', '', 1).isdigit()) else float(cfg.get("rate_per_sec", 5.0))
    set_mode = (os.getenv("A2DEV_SET") or str(cfg.get("set", "auto"))).lower()
    return {"parallel": par, "cache": cache, "ttl_minutes": ttl, "max_workers": maxw, "rate_per_sec": rps, "set": set_mode}


def get_progressive_targets() -> list[str] | None:
    """Return a list of target keys when progressive set is requested; otherwise None for 'auto' (all)."""
    s = get_perf_flags().get("set", "auto")
    if s == "minimal":
        return ["ux", "shard"]
    if s == "standard":
        return ["ux", "arch", "nfrs", "plan", "qa", "shard"]
    if s == "complete":
        return ["ux", "arch", "nfrs", "plan", "qa", "security", "devops", "release", "observability", "data", "trace", "shard", "a11y", "hypothesis"]
    return None


def get_orchestrator():
    """Factory that chooses base vs parallel orchestrator by flags.

    Returns an object exposing prepare_story(story_id, also_scaffold=False).
    """
    from ..orchestrator import Orchestrator as _Base
    flags = get_perf_flags()
    if flags.get("parallel") in {"on", "auto"}:
        try:
            from .parallel import ParallelOrchestrator as _Par
            maxw = flags.get("max_workers") or None
            return _Par(max_workers=maxw, rate_per_sec=flags.get("rate_per_sec"))
        except Exception:
            return _Base()
    return _Base()


def set_mode(value: str) -> str:
    """Set A2Dev mode to 'on' or 'off' by updating .a2dev/mode.yaml.

    Returns the effective mode after the update.
    """
    value = str(value).strip().lower()
    root = project_root()
    path = root / ".a2dev" / "mode.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    data: Dict[str, Any] = {"a2dev_mode": value}
    # Try to preserve other fields if PyYAML is available
    try:
        import yaml  # type: ignore
        existing = read_yaml(path)
        existing["a2dev_mode"] = value
        path.write_text(yaml.safe_dump(existing, sort_keys=True))
    except Exception:
        path.write_text(f"a2dev_mode: {value}\n")
    return value


def toggle_mode() -> str:
    current = str(get_mode_flags().get("a2dev_mode", "on")).lower()
    newv = "off" if current == "on" else "on"
    return set_mode(newv)
