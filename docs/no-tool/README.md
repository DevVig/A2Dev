# No‑Tool Mode — A2Dev

This guide lets you work entirely by instructions (no CLI calls). Agents output artifacts inline; you save them to the indicated paths.

Inline Artifact Protocol
- Begin: `>>> BEGIN: <relative/file/path>`
- Content: file body
- End: `>>> END`

Standard Locations
- PRD: `docs/PRD.md`
- Backlog: `docs/backlog.json` (see `.a2dev/templates/backlog.json`)
- Epics index: `docs/epics.md`
- Status board: `docs/status/board.md` (see `.a2dev/templates/status/board.md`)
- Story hub: `docs/stories/story-<id>.md` (includes “Status & Ownership” section)
- Per‑story: UX/ADR/Plan/QA/Threat/DevOps/Data/Trace under `docs/**` (templates under `.a2dev/templates/**`)
- QA readiness: `docs/qa/readiness/story-<id>.md`
- Privacy review: `docs/security/privacy/story-<id>.md` (if analytics PII != none)
- Timeline (optional): `docs/timeline/assess.md`, `docs/timeline/story-<id>.md`

Typical Flow
1) `@analyst` → greet + choose path. Output `docs/PRD.md` inline using `.a2dev/templates/prd.md`. Save it.
2) Analyst outputs `docs/backlog.json` inline (follow schema in `.a2dev/templates/backlog.json`). Save it. Optionally output `docs/epics.md`.
3) `@pm` → choose a story ID. For each story, PM directs generation of: UX, ADR, Plan, QA, Threat, DevOps, Data, Trace, and Story hub — all inline using templates. Save each file.
4) Manual Gate (checklist): verify presence of all artifacts for the story; if Analytics PII != none, also add a privacy review. Decide PASS/FAIL.
5) Update Status:
   - Story file: edit “Status & Ownership” (Phase, Owner, Next, Gate, Last Updated).
   - Backlog: update story fields (phase/owner/next_owner/gate) in `docs/backlog.json`.
   - Board: regenerate `docs/status/board.md` inline as a table.
6) QA: create/update `docs/qa/readiness/story-<id>.md`. When ready, set Ready: yes, Gate: PASS.
7) `@spm`: perform sustain checks using the same checklist philosophy; update status and board.

Manual Gate Checklist (Summary)
- Acceptance criteria exist for the story in backlog.
- Required artifacts present: UX, ADR, Deep Plan, QA Plan, Threat Model, DevOps Plan, Analytics Spec, Trace, Story hub.
- Analytics PII: if not “none”, ensure a Privacy Review is created.
- Optional checks: add Semgrep/Secrets placeholder notes if scans cannot run.

Notes
- Always end agent replies with the standard status line.
- Use numbered steps and explicit file paths to keep the process deterministic.
