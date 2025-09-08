from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict

from ..orchestrator import Orchestrator
from .ratelimit import RateLimiter


class ParallelOrchestrator:
    """Thin wrapper to prepare a story using limited parallelism.

    Initial version defers to the existing Orchestrator while providing a
    structure for future parallel execution with dependency awareness.
    """

    def __init__(self, max_workers: int | None = None, rate_per_sec: float | None = None) -> None:
        self.base = Orchestrator()
        self.max_workers = max_workers
        self.rl = RateLimiter(rate_per_sec=rate_per_sec or 5.0)

    def _run_parallel(self, tasks: Dict[str, Callable[[], Any]]) -> Dict[str, Any]:
        if not tasks:
            return {}
        results: Dict[str, Any] = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            fut_map = {}
            for name, fn in tasks.items():
                try:
                    self.rl.acquire()
                except Exception:
                    pass
                fut_map[pool.submit(fn)] = name
            for fut in as_completed(fut_map):
                name = fut_map[fut]
                try:
                    results[name] = fut.result()
                except Exception as e:  # noqa: BLE001
                    results[name] = {"error": str(e)}
        return results

    def prepare_story(self, story_id: int, also_scaffold: bool = False) -> Dict[str, Any]:
        # Phase 1: delegate to existing orchestrator (sequential).
        # Future: split independent steps and execute via _run_parallel.
        return self.base.prepare_story(story_id, also_scaffold=also_scaffold)
