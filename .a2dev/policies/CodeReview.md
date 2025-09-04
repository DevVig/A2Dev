Code Review Checklist

- Purpose: change aligns to story/bug and scoped minimally.
- Correctness: logic is sound; edge cases considered; tests added/updated.
- Readability: clear flow; good names; comments where needed.
- Security: inputs validated; authn/z respected; secrets not exposed.
- Privacy: data classification respected; PII minimized and protected.
- Observability: logging/tracing adequate; errors actionable.
- Dependencies: vetted; pinned appropriately; no unnecessary additions.
- Performance: hot paths considered where relevant; no N+1 queries.
- Docs: user/dev docs updated if behavior changes.
- Risk: migration/rollback plan where applicable.

