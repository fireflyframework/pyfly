"""In-memory event bus for testing and single-process applications."""

from __future__ import annotations

import fnmatch
from typing import Any

from pyfly.eda.bus import EventHandler
from pyfly.eda.types import EventEnvelope


class InMemoryEventBus:
    """In-memory event bus using pattern-matched subscriptions.

    Supports wildcard patterns (e.g. "user.*" matches "user.created").
    """

    def __init__(self) -> None:
        self._handlers: list[tuple[str, EventHandler]] = []

    def subscribe(self, event_type_pattern: str, handler: EventHandler) -> None:
        """Subscribe a handler to events matching the pattern."""
        self._handlers.append((event_type_pattern, handler))

    async def publish(
        self,
        destination: str,
        event_type: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> None:
        """Publish an event to all matching subscribers."""
        envelope = EventEnvelope(
            event_type=event_type,
            payload=payload,
            destination=destination,
            headers=headers or {},
        )
        for pattern, handler in self._handlers:
            if fnmatch.fnmatch(event_type, pattern):
                await handler(envelope)
