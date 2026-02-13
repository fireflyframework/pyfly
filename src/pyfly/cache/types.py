"""Cache adapter protocol."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CacheAdapter(Protocol):
    """Abstract cache interface.

    All cache backends (Redis, in-memory, etc.) must implement this protocol.
    """

    async def get(self, key: str) -> Any | None: ...

    async def put(self, key: str, value: Any, ttl: timedelta | None = None) -> None: ...

    async def evict(self, key: str) -> bool: ...

    async def clear(self) -> None: ...
