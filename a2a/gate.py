from __future__ import annotations

from pathlib import Path
from .schema import Backlog
from .quality import semgrep_summary


def gate_story(backlog: Backlog, story_id: int) -> tuple[bool, list[str], list[str]]:
    story = next((s for e in backlog.epics for s in e.stories if s.id == story_id), None)
    if not story:
        return False, [f"Story {story_id} not found"]

    missing: list[str] = []
    checked_paths: list[str] = []
    if not story.acceptance_criteria:
        missing.append("Acceptance criteria missing")

    checks = {
        "UX": Path(f"docs/ux/story-{story_id}.md"),
        "ADR": Path(f"docs/architecture/ADR-story-{story_id}.md"),
        "Deep Plan": Path(f"docs/planning/story-{story_id}.md"),
        "QA Plan": Path(f"docs/qa/plans/story-{story_id}.md"),
        "Traceability": Path(f"docs/qa/trace/story-{story_id}.md"),
        "Threat Model": Path(f"docs/security/threats/story-{story_id}.md"),
        "DevOps Plan": Path(f"docs/devops/story-{story_id}.md"),
        "Analytics Spec": Path(f"docs/data/analytics/story-{story_id}.md"),
        "Story Shard": Path(f"docs/stories/story-{story_id}.md"),
    }

    for name, path in checks.items():
        checked_paths.append(str(path))
        if not path.exists():
            missing.append(f"Missing {name}: {path}")

    # Semgrep high severity must be zero if report exists
    semgrep_json = Path(f"docs/security/semgrep/story-{story_id}.json")
    if semgrep_json.exists():
        high, med, low = semgrep_summary(semgrep_json)
        if high > 0:
            missing.append(f"Semgrep high-severity findings: {high}")

    # Secrets scan must be empty if report exists
    secrets_json = Path(f"docs/security/secrets/story-{story_id}.json")
    if secrets_json.exists():
        try:
            data = __import__("json").loads(secrets_json.read_text())
            findings = data.get("findings", data if isinstance(data, list) else [])
            if isinstance(findings, list) and len(findings) > 0:
                missing.append(f"Secrets findings detected: {len(findings)}")
        except Exception:
            pass

    # Privacy check from Analytics spec
    _analytics_privacy_check(story_id, checked_paths, missing)

    # Risk-based checks
    risk_path = Path(f"docs/qa/risk/story-{story_id}.json")
    if risk_path.exists():
        try:
            import json as _json
            level = _json.loads(risk_path.read_text()).get("level", "low").lower()
            if level == "high":
                design_doc = Path(f"docs/qa/design/story-{story_id}.md")
                checked_paths.append(str(design_doc))
                if not design_doc.exists():
                    missing.append("Missing QA Design Review for high-risk story")
                # Architecture review and runbook required for high-risk stories
                arch_review = Path(f"docs/architecture/reviews/story-{story_id}.md")
                devops_runbook = Path(f"docs/devops/runbooks/story-{story_id}.md")
                checked_paths += [str(arch_review), str(devops_runbook)]
                if not arch_review.exists():
                    missing.append("Missing Architecture Review for high-risk story")
                if not devops_runbook.exists():
                    missing.append("Missing DevOps Runbook for high-risk story")
        except Exception:
            missing.append("Invalid risk file format")

    return len(missing) == 0, missing, checked_paths

def _analytics_privacy_check(story_id: int, checked_paths: list[str], missing: list[str]) -> None:
    """If analytics spec declares PII other than 'none', require a privacy review doc."""
    a_path = Path(f"docs/data/analytics/story-{story_id}.md")
    if not a_path.exists():
        return
    try:
        text = a_path.read_text().lower()
    except Exception:
        return
    pii_level = None
    for ln in text.splitlines():
        if ln.strip().startswith("- pii:") or ln.strip().startswith("pii:"):
            pii_level = ln.split(":", 1)[1].strip()
            break
    if pii_level and pii_level not in {"none", "none|minimal", "none|minimal"} and not pii_level.startswith("none"):
        priv = Path(f"docs/security/privacy/story-{story_id}.md")
        checked_paths.append(str(priv))
        if not priv.exists():
            missing.append("Missing Privacy Review for analytics PII")
