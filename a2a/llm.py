from __future__ import annotations

import os
from typing import Optional

from .models import ModelProfile, select_model


class LLMClient:
    """Thin abstraction with provider routing.

    This is a placeholder: wire real SDKs where noted.
    """

    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def complete(
        self,
        prompt: str,
        task: str,
        system: Optional[str] = None,
        prefer: Optional[str] = None,
        max_tokens: int = 2000,
        tier: Optional[str] = None,
    ) -> str:
        model: ModelProfile = select_model(
            task=task,
            need_long_context=len(prompt) > 20000,
            prefer=prefer,
            tier=tier,
        )
        # NOTE: Replace the mock return with real provider calls as needed.
        # For safety, we keep this as a stub to avoid network calls by default.
        header = f"[model={model.name} provider={model.provider} task={task}]"
        return f"{header}\n\n(Stubbed LLM output)\n\n{prompt[:500]}..."
