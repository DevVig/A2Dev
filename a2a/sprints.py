from __future__ import annotations

from pathlib import Path
from typing import List

from .schema import Backlog, Story, Priority


def _story_points(story: Story) -> float:
    return float(story.estimate or 1.0)


def plan_sprints(backlog: Backlog, capacity: float = 20.0, weeks: int = 2) -> List[List[Story]]:
    # Simple greedy pack by priority (must → should → could), then by id
    bucketed = {Priority.must: [], Priority.should: [], Priority.could: []}
    for e in backlog.epics:
        for s in e.stories:
            bucketed.get(s.priority, bucketed[Priority.should]).append(s)

    ordered = bucketed[Priority.must] + bucketed[Priority.should] + bucketed[Priority.could]
    sprints: List[List[Story]] = []
    current: List[Story] = []
    used = 0.0
    for s in ordered:
        pts = _story_points(s)
        if used + pts <= capacity:
            current.append(s)
            used += pts
        else:
            if current:
                sprints.append(current)
            current = [s]
            used = pts
    if current:
        sprints.append(current)
    return sprints


def write_sprints(backlog: Backlog, capacity: float = 20.0, weeks: int = 2) -> str:
    sprints = plan_sprints(backlog, capacity=capacity, weeks=weeks)
    base = Path("docs/sprints")
    base.mkdir(parents=True, exist_ok=True)
    index_lines = [f"# Sprint Plan (capacity={capacity}, length={weeks}w)", ""]
    for i, sp in enumerate(sprints, start=1):
        pts = sum(_story_points(s) for s in sp)
        md = [f"# Sprint {i}", "", f"Capacity used: {pts}/{capacity}", "", "## Stories", ""]
        for s in sp:
            md.append(f"- Story {s.id}: {s.title} (pts={_story_points(s)})")
        out = base / f"sprint-{i}.md"
        out.write_text("\n".join(md))
        index_lines.append(f"- Sprint {i}: {pts}/{capacity} -> {out}")
    (base / "plan.md").write_text("\n".join(index_lines))
    return str(base / "plan.md")

