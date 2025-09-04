from __future__ import annotations

from typing import List


def analyst_assess_guidance(prd_path: str) -> str:
    return (
        "Analyst here. I’ll guide assessment (brief + backlog) before handing off to PM.\n"
        f"- Target PRD: {prd_path}\n"
        "- Choose a starting path: Fresh (create PRD), Prepared (use existing PRD), or Codebase (brownfield).\n"
        "- You can refine at any time (e.g., add ACs, rename stories).\n"
        "- Suggested replies: '@analyst assess fresh' | '@analyst assess prepared docs/PRD.md' | '@analyst assess codebase'\n"
        "- I’ll stay in Analyst mode until you switch (e.g., '@pm …') or '@analyst exit'.\n"
        "- Quick tools: 'doctor' for readiness, 'setup' for menu"
    )


def pm_develop_guidance(story_id: int) -> str:
    return (
        "PM here. I'll coordinate the sub‑agents (UX, Architect, Deep Planning, QA, Security, DevOps, Data) for this story, then run the gate.\n"
        f"- Story: {story_id}\n"
        "- Steps: UX → ADR → Deep Plan → QA → Threat → DevOps → Data → Trace → Shard → Gate.\n"
        "- If the gate fails (e.g., missing acceptance criteria), I’ll point out what to fix and we can iterate.\n"
        f"- I’ll stay in PM mode until you switch roles or '@pm exit'.\n"
        f"- Choices: (1) pm continue  (2) setup  (3) timeline {story_id}"
    )


def spm_sustain_guidance(story_id: int) -> str:
    return (
        "sPM here. I’ll verify sustainment readiness: gates, security findings, ops plan, and analytics readiness.\n"
        f"- Story: {story_id}\n"
        "- Steps: Check gate status, semgrep findings, rollout plan, and monitoring.\n"
        "- We can open follow‑ups for any gaps before marking sustainment complete.\n"
        f"- I’ll stay in sPM mode until you switch roles or '@spm exit'.\n"
        f"- Choices: (1) gate {story_id}  (2) setup  (3) timeline {story_id}"
    )


def pm_gate_feedback(gate_ok: bool, issues: List[str]) -> str:
    if gate_ok:
        return "Gate passed. Ready to proceed to implementation or PR packaging."
    items = "\n".join([f"- {i}" for i in issues])
    return (
        "Gate failed. Let’s resolve the following before implementation:\n"
        f"{items}\n"
        "Options: add/update ACs, regenerate artifacts, or adjust scope."
    )
