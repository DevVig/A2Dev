from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict


class SmartCache:
    """Content/env-keyed cache with TTL and basic file locking.

    Minimal, safe-by-default implementation; not wired into orchestrator yet.
    """

    def __init__(self, cache_dir: str | Path = ".a2dev/cache", ttl_minutes: int = 60) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(minutes=ttl_minutes)

    def _lock_path(self, key: str) -> Path:
        h = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{h}.lock"

    def _data_path(self, key: str) -> Path:
        h = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{h}.json"

    def _with_lock(self, lock_path: Path, fn: Callable[[], Any]) -> Any:
        # Simple advisory lock using os.open + exclusive create
        lock_fd = None
        try:
            try:
                lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                # Best-effort wait + fallthrough
                return fn()
            return fn()
        finally:
            if lock_fd is not None:
                try:
                    os.close(lock_fd)
                    os.unlink(lock_path)
                except Exception:
                    pass

    def get_or_generate(self, key: str, generator: Callable[[], Any]) -> Any:
        now = datetime.utcnow()
        data_path = self._data_path(key)
        lock_path = self._lock_path(key)

        def _read() -> Dict[str, Any] | None:
            try:
                if not data_path.exists():
                    return None
                obj = json.loads(data_path.read_text())
                ts = datetime.fromisoformat(obj.get("timestamp", now.isoformat()))
                if now - ts > self.ttl:
                    return None
                return obj
            except Exception:
                # Treat as miss on any error
                return None

        cached = _read()
        if cached is not None:
            return cached.get("data")

        def _gen_and_write() -> Any:
            data = generator()
            payload = {"data": data, "timestamp": now.isoformat()}
            tmp = data_path.with_suffix(".tmp")
            try:
                tmp.write_text(json.dumps(payload))
                tmp.replace(data_path)
            except Exception:
                # Best effort
                pass
            return data

        return self._with_lock(lock_path, _gen_and_write)

