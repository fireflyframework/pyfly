"""Outbound port protocols for event-driven architecture."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol, runtime_checkable

from pyfly.eda.types import EventEnvelope

EventHandler = Callable[[EventEnvelope], Awaitable[None]]


@runtime_checkable
class EventPublisher(Protocol):
    """Abstract event publisher interface."""

    def subscribe(self, event_type_pattern: str, handler: EventHandler) -> None: ...

    async def publish(
        self,
        destination: str,
        event_type: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> None: ...


@runtime_checkable
class EventConsumer(Protocol):
    """Abstract event consumer interface."""

    async def start(self) -> None: ...

    async def stop(self) -> None: ...
