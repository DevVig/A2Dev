from __future__ import annotations

from pathlib import Path
from .schema import Backlog


def generate_trace(backlog: Backlog, story_id: int) -> str:
    story = next((s for e in backlog.epics for s in e.stories if s.id == story_id), None)
    if not story:
        raise ValueError(f"Story {story_id} not found")

    qa_plan = Path(f"docs/qa/plans/story-{story_id}.md")
    rows = []
    for idx, ac in enumerate(story.acceptance_criteria or ["TBD" ], start=1):
        rows.append((f"AC-{story_id}-{idx}", ac, f"TC-{story_id}-{idx}", "Draft"))

    lines = [
        f"# Requirements Traceability — Story {story_id}",
        "",
        f"QA Plan: {qa_plan if qa_plan.exists() else 'TBD'}",
        "",
        "| AC ID | Acceptance Criterion | Test Case ID | Status |",
        "|-------|----------------------|--------------|--------|",
    ]
    for ac_id, ac_text, tc_id, status in rows:
        lines.append(f"| {ac_id} | {ac_text} | {tc_id} | {status} |")

    out_dir = Path("docs/qa/trace")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"story-{story_id}.md"
    out.write_text("\n".join(lines))
    return str(out)

