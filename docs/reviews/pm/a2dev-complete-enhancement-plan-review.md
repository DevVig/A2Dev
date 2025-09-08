# PM Review — A2Dev Complete Enhancement Plan

Date: 2025-09-07
Reviewer: PM
Source: docs/proposals/a2dev-complete-enhancement-plan.md

## Summary Assessment
- Status: Review — conditional approval with required clarifications and minor fixes.
- Overall: Strong proposal with clear layered strategy, compelling performance focus, and good risk awareness. Needs tighter gate criteria, benchmarking protocol, and a few correctness/operability fixes before greenlighting Phase 1.

## Strengths
- Clear separation of concerns: optional intelligence layer with zero-impact toggle.
- Performance-centric roadmap (parallelism, caching, progressive sets) aligned with user value.
- Practical migration paths (BMAD → A2Dev) reduce adoption friction.
- Sensible scope for core (LOC budget, deletable intelligence layer) to prevent complexity creep.

## Risks & Concerns
1) Performance claims depend on safe concurrency and stable baselines
   - Impact: High — parallel LLM calls can hit rate limits, ordering, and token budgeting issues.
   - Ask: Add a rate-limit/backoff layer, bounded worker pool, and idempotent orchestration with dependency graph. Define baseline benchmarks before changes.

2) Caching design and invalidation
   - Impact: High — example uses a generic `key` and `compute_hash(key)`; needs content- and environment-derived keys.
   - Ask: Include prompt/template version, model name, PRD/backlog hashes, story ID, env flags, and intelligence toggle in cache key. Add file locking (cross-platform) and corruption handling.

3) Example bug in retrospectives
   - Impact: Medium — `retro_dir / f"sprint_{sprint}.json"` references undefined `sprint`; should use `template['sprint']`.

4) Gate invariants with intelligence layer
   - Impact: Medium — enhanced personas/workflows may change outputs; gates must remain consistent.
   - Ask: Add golden tests to assert gate-input invariants when intelligence is ON vs OFF.

5) DevOps/CI reproducibility for perf budgets
   - Impact: Medium — benchmarks can be noisy across runners.
   - Ask: Establish a deterministic benchmark harness with fixed seed inputs, warm cache/cold cache scenarios, and tolerance bands.

6) CLI surface vs plan
   - Impact: Medium — commands like `enhance`, `metrics`, `migrate-from-bmad` need RFCs, help text, and backward-compatible aliases.

7) Privacy & security artifacts
   - Impact: Medium — include privacy assessment when analytics/PII is present; threat model is listed, but privacy doc is not called out in deliverables.

## Gaps & Questions
- NFRs: Add an NFRs document (performance, reliability, security, privacy, observability) and tie each target to tests.
- Observability & Release: Include explicit Observability Plan and Release Plan deliverables (SLOs, alerts, rollback).
- DORA: Optional but recommended tracking (deployment frequency, lead time, MTTR, change failure rate).
- Memory target (<100MB): Clarify measurement method and scope (with/without caches, dataset size). Consider a percentile target.
- Migration: Confirm scope for BMAD config coverage and failure modes; add a dry-run report.

## Recommendations (by Phase)
Phase 1 — Performance (Approve with additions)
1. Add benchmark harness (cold/warm cache) and publish baseline before changes.
2. Introduce a `ParallelOrchestrator` with bounded worker pool and per-provider rate limiting.
3. Implement `SmartCache` with robust key schema, file locking, and TTL.
4. Add perf budget check in CI with tolerance bands.

Phase 2 — Core Refactor (Approve)
1. Fix retro filename bug; add schema contracts for new modules.
2. Add Collaboration/Retro/Metrics behind clear interfaces; document extension points.
3. Provide Terminal dashboard first; gate web dashboard behind optional dependency group.

Phase 3 — Intelligence Layer (Gate: design ADR first)
1. Author ADR: scope, invariants, toggle semantics, deletion guarantees.
2. Add golden tests to verify behavior parity when disabled.
3. Provide minimal persona/workflow set; avoid broad port of BMAD to keep footprint small.

Phase 4 — Tests & Docs (Tighten)
1. Target >80% core initially; stretch to >90% as stable.
2. Ship CLI RFC and docs for new commands; include `--dry-run` and `--json` outputs.
3. Add migration dry-run mode with diff report.

## Gate Check (A2Dev Develop Pipeline)
- UX: Story-spec template unaffected; ok once progressive sets defined.
- ADR: REQUIRED for intelligence layer and concurrency/caching design.
- NFRs: REQUIRED — define measurable targets and test mapping.
- QA Plan: REQUIRED — include perf and cache correctness tests.
- Threat Model: REQUIRED — cover cache poisoning, temp files, concurrency.
- DevOps: REQUIRED — perf budgets in CI, rollback, observability hooks.
- Data/Analytics: REQUIRED if events added; define governance and privacy.
- Trace/Shard: Document trace IDs for artifact generation runs.
- Gate Verdict: FAIL (pending ADR, NFRs, QA, Threat, DevOps docs; perf harness).

## Acceptance Criteria (for Plan Approval)
1. ADRs: Parallel orchestration, caching strategy, intelligence toggle invariants.
2. Benchmarks: Baseline report with methodology + target budgets.
3. NFRs: Document with thresholds; CI checks wired.
4. QA/Threat/Privacy: Plans drafted with test matrix and mitigations.
5. CLI RFC: Commands, flags, backward-compat, help updates.
6. Bug fixes: Retrospective filename correction; example code validated.

## Timeline Notes
- Current 5-week plan is plausible with scope control. Recommend adding 1 buffer week (6 total) for perf tooling and CI stabilization.

## Next Steps
1. Produce ADRs (concurrency, caching, intelligence layer) and NFRs doc.
2. Add benchmark harness + publish baselines; wire CI perf budget.
3. Update proposal with acceptance criteria and adjusted timeline (6 weeks).
4. PM to re-run gate after ADR/NFR/QA/Threat/DevOps docs are added.

— End of PM Review —

