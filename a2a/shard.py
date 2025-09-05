from __future__ import annotations

from pathlib import Path
from datetime import datetime
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


def update_story_status(
    story_id: int,
    *,
    phase: str,
    owner: str,
    next_owner: str,
    gate: str | None = None,
) -> str:
    """Insert or update a 'Status & Ownership' section in the story file.

    The section is bounded by a '## Status & Ownership' header up to the next '## ' header
    or end-of-file.
    """
    out = Path(f"docs/stories/story-{story_id}.md")
    if not out.exists():
        return ""
    ts = datetime.utcnow().isoformat() + "Z"
    status_lines = [
        "## Status & Ownership",
        f"- Phase: {phase}",
        f"- Owner: {owner}",
        f"- Next: {next_owner}",
        f"- Gate: {gate if gate is not None else 'n/a'}",
        f"- Last Updated: {ts}",
        "",
    ]
    text = out.read_text()
    lines = text.splitlines()
    # Find existing section
    start = None
    end = None
    for i, ln in enumerate(lines):
        if ln.strip().lower().startswith("## status & ownership"):
            start = i
            # find end as next heading starting with '## '
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("## "):
                    end = j
                    break
            if end is None:
                end = len(lines)
            break
    new_block = "\n".join(status_lines)
    if start is None:
        # Insert after Linked Artifacts section if present, else at end
        insert_at = len(lines)
        for i, ln in enumerate(lines):
            if ln.strip().lower().startswith("## linked artifacts"):
                # place after that section block
                insert_at = i + 1
                # skip to end of that section (until next heading)
                for j in range(insert_at, len(lines)):
                    if lines[j].startswith("## "):
                        insert_at = j
                        break
                break
        new_text = "\n".join(lines[:insert_at] + [new_block] + lines[insert_at:]) + ("\n" if not text.endswith("\n") else "")
    else:
        new_text = "\n".join(lines[:start] + [new_block] + lines[end:]) + ("\n" if not text.endswith("\n") else "")
    out.write_text(new_text)
    return str(out)
