"""httpx-based HTTP client adapter."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import httpx


class HttpxClientAdapter:
    """HTTP client adapter backed by httpx.AsyncClient."""

    def __init__(
        self,
        base_url: str = "",
        timeout: timedelta = timedelta(seconds=30),
        headers: dict[str, str] | None = None,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout.total_seconds(),
            headers=headers or {},
        )

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        return await self._client.request(method, url, **kwargs)

    async def close(self) -> None:
        await self._client.aclose()
