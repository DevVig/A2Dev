from __future__ import annotations

from pathlib import Path
from ..schema import Backlog


class SecurityRole:
    def threat_model_for_story(self, backlog: Backlog, story_id: int) -> str:
        story = next((s for e in backlog.epics for s in e.stories if s.id == story_id), None)
        if not story:
            raise ValueError(f"Story {story_id} not found")
        return f"""# Threat Model — Story {story.id}: {story.title}

## Data Classification
- TBD (PII/PHI/Secrets/None)

## Assets & Entry Points
- UI forms, APIs, storage, integrations

## Threats (STRIDE)
- Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege

## Controls
- Authentication, authorization, input validation, logging, rate limiting, encryption (at rest/in transit)

## Residual Risk
- TBD
"""

    def write_threat_model(self, text: str, story_id: int) -> str:
        out_dir = Path("docs/security/threats")
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"story-{story_id}.md"
        out.write_text(text)
        return str(out)

