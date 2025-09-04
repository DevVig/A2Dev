from __future__ import annotations

from pathlib import Path
from .schema import Backlog


def shard_story(backlog: Backlog, story_id: int) -> str:
    story = next((s for e in backlog.epics for s in e.stories if s.id == story_id), None)
    if not story:
        raise ValueError(f"Story {story_id} not found")

    ux_path = Path(f"docs/ux/story-{story_id}.md")
    adr_path = Path(f"docs/architecture/ADR-story-{story_id}.md")
    deep_plan_path = Path(f"docs/planning/story-{story_id}.md")
    qa_plan_path = Path(f"docs/qa/plans/story-{story_id}.md")
    threat_path = Path(f"docs/security/threats/story-{story_id}.md")
    devops_path = Path(f"docs/devops/story-{story_id}.md")
    data_path = Path(f"docs/data/analytics/story-{story_id}.md")
    semgrep_path = Path(f"docs/security/semgrep/story-{story_id}.json")
    secrets_path = Path(f"docs/security/secrets/story-{story_id}.json")

    ac_lines = "\n".join([f"- {a}" for a in story.acceptance_criteria]) or "- TBD"

    lines = [
        f"# Story {story.id}: {story.title}",
        "",
        "## Summary",
        story.description or "TBD",
        "",
        "## Acceptance Criteria",
        ac_lines,
        "",
        "## Linked Artifacts",
        f"- UX: {ux_path if ux_path.exists() else 'TBD'}",
        f"- ADR: {adr_path if adr_path.exists() else 'TBD'}",
        f"- Deep Plan: {deep_plan_path if deep_plan_path.exists() else 'TBD'}",
        f"- QA Plan: {qa_plan_path if qa_plan_path.exists() else 'TBD'}",
        f"- Threat Model: {threat_path if threat_path.exists() else 'TBD'}",
        f"- DevOps Plan: {devops_path if devops_path.exists() else 'TBD'}",
        f"- Analytics Spec: {data_path if data_path.exists() else 'TBD'}",
        f"- Semgrep Findings: {semgrep_path if semgrep_path.exists() else 'TBD'}",
        f"- Secrets Findings: {secrets_path if secrets_path.exists() else 'TBD'}",
        "",
        "## Tasks (Checklist)",
        "- [ ] Implement feature",
        "- [ ] Update docs",
        "- [ ] Tests pass (unit/integration/e2e)",
        "- [ ] Security/Privacy checks",
        "- [ ] Analytics implemented",
        "- [ ] Rollout plan prepared",
    ]

    out_dir = Path("docs/stories")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"story-{story_id}.md"
    out.write_text("\n".join(lines))
    return str(out)
