import json
from pathlib import Path
from typing import Optional

from .schema import Backlog, State, UXDoc


def ensure_dirs():
    Path(".a2dev").mkdir(parents=True, exist_ok=True)
    Path("docs").mkdir(parents=True, exist_ok=True)
    Path("docs/ux").mkdir(parents=True, exist_ok=True)
    Path("features").mkdir(parents=True, exist_ok=True)


def write_backlog(backlog: Backlog, path: str = "docs/backlog.json") -> None:
    ensure_dirs()
    Path(path).write_text(backlog.to_json())


def read_backlog(path: str = "docs/backlog.json") -> Optional[Backlog]:
    p = Path(path)
    if not p.exists():
        return None
    return Backlog.from_json(p.read_text())


def write_epics_md(backlog: Backlog, path: str = "docs/epics.md") -> None:
    lines = ["# Epics and Stories\n"]
    for epic in backlog.epics:
        lines.append(f"\n## {epic.id}. {epic.title}\n\n{epic.description}\n")
        for story in epic.stories:
            ac = "\n".join([f"  - {a}" for a in story.acceptance_criteria])
            lines.append(
                f"- Story {story.id}: {story.title}\n  - Priority: {story.priority}\n  - Estimate: {story.estimate}\n  - Acceptance Criteria:\n{ac if ac else '  - TBD'}\n"
            )
    Path(path).write_text("\n".join(lines))


def write_ux_doc(doc: UXDoc, dir_path: str = "docs/ux") -> str:
    ensure_dirs()
    p = Path(dir_path) / f"story-{doc.story_id}.md"
    lines = [
        f"# UX Spec — Story {doc.story_id}: {doc.title}",
        "",
        "## Flows",
    ]
    lines += [f"- {f}" for f in doc.flows] or ["- TBD"]
    lines += [
        "",
        "## States",
    ]
    lines += [f"- {s}" for s in doc.states] or ["- TBD"]
    lines += [
        "",
        "## Validations",
    ]
    lines += [f"- {v}" for v in doc.validations] or ["- TBD"]
    lines += [
        "",
        "## Notes",
    ]
    lines += [f"- {n}" for n in doc.notes] or ["- None"]
    p.write_text("\n".join(lines))
    return str(p)


def read_state(path: str = ".a2dev/state.json") -> State:
    p = Path(path)
    if not p.exists():
        s = State()
        write_state(s, path)
        return s
    data = json.loads(p.read_text())
    return State(**data)


def write_state(state: State, path: str = ".a2dev/state.json") -> None:
    Path(path).write_text(json.dumps(state.__dict__, indent=2))
