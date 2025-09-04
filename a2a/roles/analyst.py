from __future__ import annotations

from pathlib import Path


class AnalystRole:
    def brief_from_prd(self, prd_path: str) -> str:
        text = Path(prd_path).read_text() if Path(prd_path).exists() else ""
        return f"""# Project Brief

## Summary
- High-level overview extracted from PRD.

## Goals
- Business and user goals.

## Scope
- In scope / Out of scope.

## Context
{text[:1000]}{'...' if len(text) > 1000 else ''}
"""

    def research(self, topic: str) -> str:
        return f"""# Analyst Research

## Topic
{topic}

## Market Overview
- TBD

## User Segments
- TBD

## Risks & Opportunities
- TBD
"""

    def competitors(self, topic: str) -> str:
        return f"""# Competitor Analysis

## Topic
{topic}

## Competitors
- TBD

## Differentiators
- TBD

## Risks
- TBD
"""

    def write(self, name: str, text: str) -> str:
        out_dir = Path("docs/analyst")
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"{name}.md"
        out.write_text(text)
        return str(out)

    def questions(self) -> str:
        return """# Open Questions

- Users, roles, and goals?
- Environments and platforms?
- Constraints (legal/compliance/tech)?
- Success metrics?
- Out of scope?
"""

    def assumptions(self) -> str:
        return """# Assumptions & Out of Scope

- Key assumptions
- Explicit exclusions
"""

    def success_metrics(self) -> str:
        return """# Success Metrics

- Business and user KPIs
- Leading indicators
- North-star metric
"""

    def stakeholders(self) -> str:
        return """# Stakeholders

- Roles, responsibilities, and contact
"""

    def links(self) -> str:
        return """# Reference Links

- Research, benchmarks, competition, prior art
"""

    def prd_template(self, project_name: str | None = None) -> str:
        name = project_name or "Project"
        return f"""# Product Requirements Document — {name}

## Summary
- One-paragraph description, target users, and value proposition.

## Goals & Success Metrics
- Business and user KPIs; leading indicators.

## Users & Personas
- Roles, needs, accessibility considerations.

## Functional Requirements
- Feature list with brief descriptions.

## Non-Functional Requirements (NFRs)
- Performance, reliability, security, privacy, observability.

## Epics & Stories
- Epics with stories; each story has acceptance criteria.

## Constraints & Assumptions
- Legal/compliance, tech constraints, explicit assumptions.

## Dependencies & Risks
- Integrations, sequencing, known risks and mitigations.

## Analytics & Telemetry
- Events, properties, dashboards, KPIs.

## Rollout Plan
- Environments, feature flags, migration/rollback, monitoring.
"""

    def viability_assessment(self, prd_path: str, audience: str = "both") -> str:
        from pathlib import Path
        prd_txt = Path(prd_path).read_text() if Path(prd_path).exists() else ""
        lines = [f"# Viability Assessment", ""]
        if audience in ("internal", "both"):
            lines += [
                "## Internal Viability",
                "- Strategic alignment and priority",
                "- Resourcing and skills availability",
                "- Technical feasibility and stack fit",
                "- Opportunity cost and dependencies",
                "",
            ]
        if audience in ("external", "both"):
            lines += [
                "## External Viability",
                "- Market need and urgency",
                "- Competitor landscape and differentiation",
                "- Regulatory/compliance impact",
                "- Monetization/ROI considerations",
                "",
            ]
        lines += [
            "## Risks & Mitigations",
            "- Top risks with proposed mitigations",
            "",
            "## Summary & Recommendation",
            "- Build / Not now / Explore further",
            "",
            "## Appendix — PRD Excerpt",
            prd_txt[:1000] + ("..." if len(prd_txt) > 1000 else ""),
        ]
        return "\n".join(lines)
