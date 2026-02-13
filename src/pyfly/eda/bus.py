"""Event bus protocol defining the publish/subscribe contract."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Protocol

from pyfly.eda.types import EventEnvelope

EventHandler = Callable[[EventEnvelope], Awaitable[None]]


class EventBus(Protocol):
    """Abstract event bus interface."""

    def subscribe(self, event_type_pattern: str, handler: EventHandler) -> None: ...

    async def publish(
        self,
        destination: str,
        event_type: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> None: ...
