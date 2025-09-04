from __future__ import annotations

from pathlib import Path
from ..schema import Backlog


class DevOpsRole:
    def plan_for_story(self, backlog: Backlog, story_id: int) -> str:
        story = next((s for e in backlog.epics for s in e.stories if s.id == story_id), None)
        if not story:
            raise ValueError(f"Story {story_id} not found")
        return f"""# DevOps Plan — Story {story.id}: {story.title}

## Environments
- Dev, Staging, Prod

## CI/CD
- Build, test, lint, security scan, deploy

## Observability
- Metrics, logs, traces, alerts

## Rollout Strategy
- Feature flags, canary, rollback

## Infrastructure Changes
- TBD
"""

    def write_plan(self, text: str, story_id: int) -> str:
        out_dir = Path("docs/devops")
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"story-{story_id}.md"
        out.write_text(text)
        return str(out)

    def write_runbook(self, story_id: int) -> str:
        out_dir = Path("docs/devops/runbooks")
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"story-{story_id}.md"
        # Load template if present
        tpl = Path(".a2dev/templates/devops/runbook.md")
        if tpl.exists():
            txt = tpl.read_text().replace("{{id}}", str(story_id))
        else:
            txt = f"# Service Runbook — Story {story_id}\n\n- Owners, SLIs/SLOs, alerts, deploy/rollback, secrets, failure modes.\n"
        out.write_text(txt)
        return str(out)
