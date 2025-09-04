from __future__ import annotations

from pathlib import Path
from ..schema import Backlog


class QAPlanRole:
    def plan_for_story(self, backlog: Backlog, story_id: int) -> str:
        story = next((s for e in backlog.epics for s in e.stories if s.id == story_id), None)
        if not story:
            raise ValueError(f"Story {story_id} not found")
        ac_lines = "\n".join([f"- {a}" for a in story.acceptance_criteria]) or "- TBD"
        return f"""# QA Test Plan — Story {story.id}: {story.title}

## Scope
- Functional verification against acceptance criteria

## Acceptance Criteria
{ac_lines}

## Test Levels
- Unit: functions/classes
- Integration: module boundaries
- E2E: user flows

## Test Cases (Draft)
- TBD

## Non-Functional
- Performance, accessibility, security smoke, reliability (as applicable)

## Traceability Matrix (Draft)
- Map AC → TestCase IDs
"""

    def write_plan(self, text: str, story_id: int) -> str:
        out_dir = Path("docs/qa/plans")
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"story-{story_id}.md"
        out.write_text(text)
        return str(out)

    def design_review(self, backlog: Backlog, story_id: int) -> str:
        story = next((s for e in backlog.epics for s in e.stories if s.id == story_id), None)
        if not story:
            raise ValueError(f"Story {story_id} not found")
        return f"""# QA Design Review — Story {story.id}: {story.title}

## Risk Assessment
- Identify high-risk areas and failure modes.

## Test Design
- Strategies per component/flow; data setup; mocks/fakes; boundary cases.

## Acceptance Criteria Mapping
- Map ACs to test cases and expected results.

## Non-Functional Considerations
- Performance, reliability, accessibility.
"""

    def write_design_review(self, text: str, story_id: int) -> str:
        out_dir = Path("docs/qa/design")
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"story-{story_id}.md"
        out.write_text(text)
        return str(out)
