from __future__ import annotations

from pathlib import Path
from ..schema import Backlog


class DataRole:
    def analytics_spec_for_story(self, backlog: Backlog, story_id: int) -> str:
        story = next((s for e in backlog.epics for s in e.stories if s.id == story_id), None)
        if not story:
            raise ValueError(f"Story {story_id} not found")
        return f"""# Analytics Spec — Story {story.id}: {story.title}

## Objectives & KPIs
- TBD

## Events & Properties
- event_name: properties

## Dashboards / Reports
- TBD

## Data Quality & Governance
- Naming, versioning, privacy
"""

    def write_spec(self, text: str, story_id: int) -> str:
        out_dir = Path("docs/data/analytics")
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"story-{story_id}.md"
        out.write_text(text)
        return str(out)

