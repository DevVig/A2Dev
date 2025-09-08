from __future__ import annotations

from typing import Dict, List

from ..orchestrator import Orchestrator


class ProgressiveOrchestrator:
    """Expose minimal/standard/complete prepares by delegating to Orchestrator.

    Initial version uses the same underlying prepare and relies on the
    orchestrator's ensure() behavior; future versions can selectively skip
    generation based on configured sets.
    """

    MINIMAL_SET: List[str] = ["ux", "story_shard"]
    STANDARD_SET: List[str] = ["ux", "arch", "qa", "story_shard"]
    COMPLETE_SET: List[str] = ["ux", "arch", "qa", "security", "devops", "data", "trace", "shard"]

    def __init__(self) -> None:
        self.base = Orchestrator()

    def _prepare_set(self, story_id: int, targets: List[str]) -> Dict[str, object]:
        # For now, call the existing orchestrator which ensures all standard
        # artifacts. Targeted generation can be added in follow-ups.
        return self.base.prepare_story(story_id, also_scaffold=False)

    def prepare_minimal(self, story_id: int) -> Dict[str, object]:
        return self._prepare_set(story_id, self.MINIMAL_SET)

    def prepare_standard(self, story_id: int) -> Dict[str, object]:
        return self._prepare_set(story_id, self.STANDARD_SET)

    def prepare_complete(self, story_id: int) -> Dict[str, object]:
        return self._prepare_set(story_id, self.COMPLETE_SET)

