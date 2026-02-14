"""Built-in cache adapter implementations."""

from __future__ import annotations

import time
from datetime import timedelta
from typing import Any


class InMemoryCache:
    """In-memory cache with optional TTL support.

    Suitable for development, testing, and single-process applications.
    Also serves as the default fallback in CacheManager.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float | None]] = {}

    async def get(self, key: str) -> Any | None:
        """Get a value by key. Returns None if missing or expired."""
        entry = self._store.get(key)
        if entry is None:
            return None

        value, expires_at = entry
        if expires_at is not None and time.monotonic() > expires_at:
            del self._store[key]
            return None

        return value

    async def put(self, key: str, value: Any, ttl: timedelta | None = None) -> None:
        """Store a value with optional TTL."""
        expires_at = None
        if ttl is not None:
            expires_at = time.monotonic() + ttl.total_seconds()
        self._store[key] = (value, expires_at)

    async def evict(self, key: str) -> bool:
        """Remove a key. Returns True if the key existed."""
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        entry = self._store.get(key)
        if entry is None:
            return False
        _, expires_at = entry
        if expires_at is not None and time.monotonic() > expires_at:
            del self._store[key]
            return False
        return True

    async def clear(self) -> None:
        """Remove all entries."""
        self._store.clear()
