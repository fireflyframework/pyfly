"""Redis-backed cache adapter."""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any


class RedisCacheAdapter:
    """Cache adapter that delegates to a ``redis.asyncio.Redis``-like client.

    Values are JSON-serialized before storage so that any JSON-compatible
    Python object can be cached transparently.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    async def get(self, key: str) -> Any | None:
        """Retrieve and deserialize a cached value."""
        raw = await self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def put(self, key: str, value: Any, ttl: timedelta | None = None) -> None:
        """Serialize and store a value with optional TTL."""
        raw = json.dumps(value)
        ex = int(ttl.total_seconds()) if ttl is not None else None
        await self._client.set(key, raw.encode(), ex=ex)

    async def evict(self, key: str) -> bool:
        """Remove a key. Returns True if the key existed."""
        count = await self._client.delete(key)
        return count > 0

    async def exists(self, key: str) -> bool:
        """Check whether a key exists."""
        count = await self._client.exists(key)
        return count > 0

    async def clear(self) -> None:
        """Flush the entire database."""
        await self._client.flushdb()

    async def close(self) -> None:
        """Close the underlying Redis connection."""
        await self._client.aclose()
