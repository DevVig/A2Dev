from __future__ import annotations

from pathlib import Path
from .schema import Backlog


def write_board(backlog: Backlog) -> str:
    """Write a simple status board of all stories with phase/owner/next/gate.

    Returns the path to the board file.
    """
    out_dir = Path("docs/status"); out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "board.md"
    lines = ["# Status Board", "", "| Epic | Story | Title | Phase | Owner | Next | Gate |", "|---|---:|---|---|---|---|---|"]
    for e in backlog.epics:
        for s in e.stories:
            lines.append(
                f"| {e.id} — {e.title} | {s.id} | {s.title} | {s.phase or '-'} | {s.owner or '-'} | {s.next_owner or '-'} | {s.gate or '-'} |"
            )
    out.write_text("\n".join(lines) + "\n")
    return str(out)


def update_story_fields(backlog: Backlog, story_id: int, *, phase: str | None = None, owner: str | None = None, next_owner: str | None = None, gate: str | None = None) -> bool:
    """Update status fields on a story in the backlog. Returns True if updated."""
    idx = {s.id: s for e in backlog.epics for s in e.stories}
    s = idx.get(story_id)
    if not s:
        return False
    if phase is not None:
        s.phase = phase
    if owner is not None:
        s.owner = owner
    if next_owner is not None:
        s.next_owner = next_owner
    if gate is not None:
        s.gate = gate
    return True

