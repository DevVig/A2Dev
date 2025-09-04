from __future__ import annotations

from pathlib import Path
from ..schema import Backlog
from ..llm import LLMClient


class DeepPlanningRole:
    def __init__(self):
        self.llm = LLMClient()

    def plan_for_story(self, backlog: Backlog, story_id: int) -> str:
        story = next((s for e in backlog.epics for s in e.stories if s.id == story_id), None)
        if not story:
            raise ValueError(f"Story {story_id} not found")
        return self._render(story_id=story.id, title=story.title, ac=story.acceptance_criteria)

    def _render(self, story_id: int, title: str, ac: list[str]) -> str:
        ac_lines = "\n".join([f"- {a}" for a in ac]) or "- TBD"
        return f"""# Deep Implementation Plan — Story {story_id}: {title}

## Objectives
- Deliver functionality per acceptance criteria.

## Acceptance Criteria (from backlog)
{ac_lines}

## Architecture & Components
- Modules, data flow, integration points.

## Data Model / Contracts
- Request/response shapes; DB schema changes.

## Test Strategy
- Unit, integration, e2e, non-functional.

## Risks & Mitigations
- TBD

## Rollout Plan
- Feature flags, migration, monitoring, rollback.
"""

