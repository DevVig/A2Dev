from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
import os


@dataclass
class ModelProfile:
    name: str
    provider: str  # e.g., openai, anthropic, ollama
    family: str    # e.g., gpt-4o, claude-3.5, llama3.1
    strengths: list[str]  # tags: planning, code, ux, security, long_context
    max_tokens: int


# Default registry (can be edited in-repo for your org)
REGISTRY: Dict[str, ModelProfile] = {
    "gpt-4o": ModelProfile(
        name="gpt-4o",
        provider="openai",
        family="gpt-4o",
        strengths=["planning", "code", "analysis", "long_context"],
        max_tokens=128000,
    ),
    "claude-3.5-sonnet": ModelProfile(
        name="claude-3.5-sonnet",
        provider="anthropic",
        family="claude-3.5-sonnet",
        strengths=["planning", "ux", "analysis", "long_context"],
        max_tokens=200000,
    ),
    "llama3.1-70b": ModelProfile(
        name="llama3.1-70b",
        provider="ollama",
        family="llama3.1-70b",
        strengths=["code", "analysis"],
        max_tokens=32000,
    ),
}


def _env_tier() -> Optional[str]:
    # Prefer A2A-specific var, fall back to Codex-like hints if present
    tier = os.getenv("A2A_MODEL_TIER") or os.getenv("CODEX_MODEL_TIER") or os.getenv("MODEL_TIER")
    if tier:
        t = tier.strip().lower()
        if t in {"high", "medium", "low"}:
            return t
    return None


def select_model(
    task: str,
    need_long_context: bool = False,
    prefer: Optional[str] = None,
    tier: Optional[str] = None,
) -> ModelProfile:
    """Heuristic model selection by task type.

    task: one of {planning, backlog, ux, architecture, design, security, code, qa, devops, docs}
    need_long_context: set True when passing large artifacts
    prefer: optional model name hint
    """
    if prefer and prefer in REGISTRY:
        return REGISTRY[prefer]

    # Simple routing logic; edit for your org policy
    if task in {"planning", "backlog", "design", "architecture", "ux"}:
        cand = [REGISTRY["claude-3.5-sonnet"], REGISTRY["gpt-4o"]]
    elif task in {"code", "qa"}:
        cand = [REGISTRY["gpt-4o"], REGISTRY["llama3.1-70b"]]
    elif task in {"security", "devops", "docs"}:
        cand = [REGISTRY["gpt-4o"], REGISTRY["claude-3.5-sonnet"]]
    else:
        cand = [REGISTRY["gpt-4o"]]

    if need_long_context:
        cand.sort(key=lambda m: m.max_tokens, reverse=True)

    # Tier routing: default to env when not provided
    tier = (tier or _env_tier() or "high").lower()
    if tier == "high":
        return cand[0]
    if tier == "medium":
        return cand[min(1, len(cand) - 1)]
    if tier == "low":
        return cand[-1]
    return cand[0]
