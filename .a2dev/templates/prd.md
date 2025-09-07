# Product Requirements Document — {{project_name}}

Note: A2Dev parses this PRD to generate epics and stories. Use the exact patterns below to ensure accurate parsing and complete artifacts.

## Summary
- One-paragraph description, target users, and value proposition.
- Problem statement and scope boundaries (what’s in / out).

## Goals & Success Metrics
- Business and user KPIs; leading indicators and guardrails.
- Success criteria (quantitative) and acceptance thresholds.

## Users & Personas (Inclusive)
- Primary and secondary personas; assistive tech users and edge cases.
- Accessibility needs (WCAG 2.1 AA), localization, and device contexts.

## Non-Functional Requirements (NFRs)
- Performance, reliability, security, privacy, observability, scalability.
- Availability targets (SLO/SLI), latency budgets, data retention, PII handling.

## Constraints & Assumptions
- Legal/compliance, data residency, architectural/tech constraints.
- Explicit assumptions and open questions.

## Dependencies & Risks
- External systems/integrations and sequencing needs.
- Known risks with mitigations and contingency triggers.

## Analytics & Telemetry
- Events, properties, governance, dashboards, KPIs.
- Data minimization and privacy notes.

## Rollout Plan
- Environments, feature flags, migration/rollback, and monitoring.

---

## Epics

Create one section per epic using a level‑2 heading. Within each epic, define stories and acceptance criteria using the exact subheadings shown.

### Example

## <Epic Name>

Overview
Short context for the epic: user need, constraints, and outcomes.

### Stories
- As a <role>, I can <capability> so that <benefit>.

### Acceptance
- Given <precondition>, When <action>, Then <outcome>.

Guidance:
- Parsing: A2Dev treats each level‑2 heading (##) as an epic.
- Under each epic, story titles are parsed from “- ” bullets that appear after a heading named “Stories”.
- Acceptance criteria are parsed from “- ” bullets that appear after a heading named “Acceptance”.
- Limitation: ACs attach to the last story in the “Stories” list in that epic. Prefer one story per epic if defining ACs here, or move ACs into docs/stories/story-<id>.md after assess.
