from __future__ import annotations

from typing import Iterable


def _shorten(paths: Iterable[str], max_items: int = 3) -> str:
    lst = list(paths)
    shown = ", ".join(p if len(p) < 40 else p[-40:] for p in lst[:max_items])
    if len(lst) > max_items:
        return f"{shown}, +{len(lst) - max_items} more"
    return shown


def format_status_line(phase: str, role: str, agents: list[str], created: list[str], referenced: list[str], gate: str | None = None) -> str:
    ag = ", ".join(agents) if agents else "-"
    c = _shorten(created) if created else "-"
    r = _shorten(referenced) if referenced else "-"
    gate_part = f" | Gate: {gate}" if gate else ""
    return f"[{phase}] {role} | Agents: {ag} | Docs +: {c} | Ref: {r}{gate_part}"

