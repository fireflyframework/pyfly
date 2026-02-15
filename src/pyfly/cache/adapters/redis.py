# Copyright 2026 Firefly Software Solutions Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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

    async def start(self) -> None:
        """Validate connectivity by pinging Redis."""
        await self._client.ping()

    async def stop(self) -> None:
        """Close the underlying Redis connection."""
        await self._client.aclose()
