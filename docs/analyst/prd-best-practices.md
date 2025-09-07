# PRD Best Practices (A2Dev)

This guide explains how to author a high‑quality, inclusive PRD that A2Dev can reliably parse into epics and stories.

## How A2Dev Parses PRDs
- Epics: every level‑2 heading (`## Epic Name`) becomes one epic.
- Stories: list items under a heading named `Stories` are parsed as story titles.
- Acceptance Criteria: list items under a heading named `Acceptance` are parsed as acceptance criteria.
- Limitation: acceptance criteria apply to the last story listed under `Stories` within that epic. If you need per‑story ACs, prefer one story per epic or assign ACs post‑generation in `docs/stories/story-<id>.md`.

### Authoring Pattern (per epic)
```
## <Epic Name>

Overview
One‑paragraph context (user need, constraints, outcomes).

### Stories
- As a <role>, I can <capability> so that <benefit>.

### Acceptance
- Given <precondition>, When <action>, Then <outcome>.
```

## Inclusive, Complete PRDs
1) Personas & A11y
   - Represent primary/secondary personas and assistive tech users.
   - Specify WCAG 2.1 AA needs early (focus order, keyboard, contrast, semantics, reduced motion).
   - Include localization, timezones, number/date formats.
2) NFRs
   - Availability/SLOs, performance budgets, security/privacy (PII), observability.
   - Data retention, export/erase requirements.
3) Constraints & Risks
   - Legal/compliance, vendor/infra limits, sequencing constraints.
   - Risk register with mitigations and monitoring triggers.
4) Analytics & Telemetry
   - Events, properties, quality checks; dashboards and decision cadence.
   - Data minimization and governance.
5) Rollout Plan
   - Environments, flags, migrations, rollback, comms, runbook links.

## Operationalization Checklist
- Write epics using `##` headings and keep each epic small/scoped.
- Use one story per epic if you want ACs captured at assess time.
- Prefer Gherkin‑style AC bullets for clarity and testability.
- After `@analyst assess docs/PRD.md`, review and refine ACs in `docs/stories/story-<id>.md`.
- Keep NFRs, privacy, and a11y explicit — the PM pipeline uses them for gates.

## Example
See `docs/PRD_SAMPLE.md` and the template at `.a2dev/templates/prd.md`.
