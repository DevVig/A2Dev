from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class RateLimiter:
    """Simple token bucket style limiter (stub).

    For now, provides a minimal sleep-based pacing API so call sites can be
    instrumented without enforcing strict limits. Wire real provider limits
    later based on perf.yaml.
    """

    rate_per_sec: float = 5.0  # tokens per second

    def __post_init__(self) -> None:
        self._last = 0.0

    def acquire(self, tokens: float = 1.0) -> None:
        now = time.monotonic()
        min_interval = tokens / max(self.rate_per_sec, 0.001)
        sleep_for = max(0.0, (self._last + min_interval) - now)
        if sleep_for > 0:
            time.sleep(sleep_for)
        self._last = time.monotonic()

