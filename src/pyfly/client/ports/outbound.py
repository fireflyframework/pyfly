"""Outbound port: HTTP client interface."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class HttpClientPort(Protocol):
    """Abstract HTTP client interface."""

    async def request(self, method: str, url: str, **kwargs: Any) -> Any: ...

    async def close(self) -> None: ...
