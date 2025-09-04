from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _ensure_dirs():
    Path(".a2dev/journal").mkdir(parents=True, exist_ok=True)
    Path("docs/timeline").mkdir(parents=True, exist_ok=True)


@dataclass
class JournalEntry:
    timestamp: str
    phase: str
    actor: str
    action: str
    story_id: Optional[int] = None
    message: Optional[str] = None
    agents_used: List[str] = field(default_factory=list)
    artifacts_created: List[str] = field(default_factory=list)
    artifacts_referenced: List[str] = field(default_factory=list)
    status: Optional[str] = None  # e.g., PASS/FAIL or summary
    extra: Dict[str, Any] = field(default_factory=dict)


def log_story_event(
    story_id: int,
    phase: str,
    actor: str,
    action: str,
    *,
    message: Optional[str] = None,
    agents_used: Optional[List[str]] = None,
    created: Optional[List[str]] = None,
    referenced: Optional[List[str]] = None,
    status: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    _ensure_dirs()
    entry = JournalEntry(
        timestamp=_ts(),
        phase=phase,
        actor=actor,
        action=action,
        story_id=story_id,
        message=message,
        agents_used=agents_used or [],
        artifacts_created=created or [],
        artifacts_referenced=referenced or [],
        status=status,
        extra=extra or {},
    )
    # Append JSONL
    jpath = Path(f".a2dev/journal/story-{story_id}.jsonl")
    with jpath.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(entry)) + "\n")
    # Append timeline line
    mpath = Path(f"docs/timeline/story-{story_id}.md")
    if not mpath.exists():
        mpath.write_text(f"# Timeline — Story {story_id}\n\n")
    line = f"- {entry.timestamp} [{phase}] {actor}: {action} ({status or '-'})\n"
    mpath.write_text(mpath.read_text() + line)


def log_assess_event(
    action: str,
    *,
    message: Optional[str] = None,
    artifacts_created: Optional[List[str]] = None,
    artifacts_referenced: Optional[List[str]] = None,
    status: Optional[str] = None,
) -> None:
    _ensure_dirs()
    entry = JournalEntry(
        timestamp=_ts(),
        phase="assess",
        actor="Analyst",
        action=action,
        message=message,
        artifacts_created=artifacts_created or [],
        artifacts_referenced=artifacts_referenced or [],
        status=status,
    )
    jpath = Path(".a2dev/journal/assess.jsonl")
    with jpath.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(entry)) + "\n")
    mpath = Path("docs/timeline/assess.md")
    if not mpath.exists():
        mpath.write_text("# Timeline — Assess\n\n")
    line = f"- {entry.timestamp} [assess] Analyst: {action} ({status or '-'})\n"
    mpath.write_text(mpath.read_text() + line)


def read_timeline(story_id: Optional[int] = None) -> str:
    if story_id is None:
        path = Path("docs/timeline/assess.md")
    else:
        path = Path(f"docs/timeline/story-{story_id}.md")
    if not path.exists():
        return "<no timeline>"
    return path.read_text()
