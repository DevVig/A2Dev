from __future__ import annotations

from pathlib import Path
from datetime import datetime
from ..schema import Backlog
from ..llm import LLMClient


class ArchitectureRole:
    def __init__(self):
        self.llm = LLMClient()

    def generate_adr(self, title: str, context: str, decision_for: str, consequences: str, prefer_model: str | None = None) -> str:
        # Use template + optional LLM augmentation
        rendered = self._render_adr(title, context, decision_for, consequences)
        # Could augment via LLM if keys exist
        return rendered

    def adr_for_story(self, backlog: Backlog, story_id: int, prefer_model: str | None = None) -> str:
        story = next((s for e in backlog.epics for s in e.stories if s.id == story_id), None)
        if not story:
            raise ValueError(f"Story {story_id} not found")
        title = f"Architecture for Story {story.id}: {story.title}"
        context = story.description or "See PRD/backlog for details."
        decision_for = "Proposed architecture options and rationale."
        consequences = "Operational and maintainability impacts."
        return self.generate_adr(title, context, decision_for, consequences, prefer_model)

    def _render_adr(self, title: str, context: str, decision_for: str, consequences: str) -> str:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return f"""# ADR: {title}

Date: {today}
Status: Proposed

## Context
{context}

## Decision
{decision_for}

## Consequences
{consequences}

## Alternatives Considered
- Option A — Pros/Cons
- Option B — Pros/Cons
- Option C — Pros/Cons

## Non-Functional Requirements
- Performance, scalability, reliability, security, observability.

## Open Questions
- TBD
"""

    def generate_architecture_doc(self, prd_path: str, project_name: str | None = None) -> str:
        from pathlib import Path
        name = project_name or Path(prd_path).stem
        prd = Path(prd_path).read_text() if Path(prd_path).exists() else ""
        return f"""# Architecture — {name}

## Overview
Summarize system goals and constraints.

## Non-Functional Requirements
- Performance, scalability, reliability, security, observability, maintainability.

## System Context
- Users, external systems, data flows, boundaries.

## Components
- Services/modules, responsibilities, interfaces, dependencies.

## Data Model
- Key entities, schemas, migrations, ownership.

## Integrations
- External services/APIs, protocols, failure modes, retries/timeouts.

## Security & Privacy
- Authn/z, data classification, encryption, secrets handling.

## Observability
- Metrics/SLIs/SLOs, logs, traces, dashboards, alerts.

## Tech Stack & Standards
- Languages, frameworks, libraries, coding standards, anti-patterns.

## Open Questions
- TBD

## Appendix — PRD Summary
{prd[:1000]}{('...' if len(prd) > 1000 else '')}
"""

    def generate_brownfield_arch(self, project_name: str | None = None) -> str:
        title = project_name or "Brownfield System"
        return f"""# Brownfield Architecture — {title}

## Current State
- High-level system map and key subsystems.

## System Boundary & Ownership
- Boundaries, domain ownership, data ownership.

## Integrations Inventory
- External/internal integrations, contracts, SLAs, failure modes.

## Risks & Tech Debt
- Known risks, deprecated components, hotspots.

## Modernization & Migration Plan
- Goals, stages, invariants, rollout plan, rollback.

## Observability & Operations
- Gaps in monitoring/alerting; operational runbooks.

## Security & Compliance
- Threat model deltas, control gaps, compliance mapping.

## Open Questions
- TBD
"""

    def write_arch_review(self, story_id: int) -> str:
        out_dir = Path("docs/architecture/reviews")
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"story-{story_id}.md"
        tpl = Path(".a2dev/templates/architecture/review.md")
        if tpl.exists():
            txt = tpl.read_text().replace("{{id}}", str(story_id))
        else:
            txt = f"# Architecture Review — Story {story_id}\n\n- Context, design, NFRs, risks, contracts, questions.\n"
        out.write_text(txt)
        return str(out)
