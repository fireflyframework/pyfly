"""CQRS middleware pipeline — cross-cutting concerns for command/query handling."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol


class CqrsMiddleware(Protocol):
    """Middleware that wraps command/query execution."""

    async def handle(self, message: Any, next_handler: Callable[..., Awaitable[Any]]) -> Any: ...


class LoggingMiddleware:
    """Logs command/query execution."""

    def __init__(self, logger: Any = None) -> None:
        self._logger = logger

    async def handle(self, message: Any, next_handler: Callable[..., Awaitable[Any]]) -> Any:
        msg_type = type(message).__name__
        if self._logger:
            self._logger.info(f"Handling {msg_type}", message_type=msg_type)
        result = await next_handler(message)
        if self._logger:
            self._logger.info(f"Completed {msg_type}", message_type=msg_type)
        return result


class MetricsMiddleware:
    """Records execution metrics for commands/queries."""

    def __init__(self, registry: Any = None) -> None:
        self._counter = registry.counter("cqrs_messages_total", "Total CQRS messages handled") if registry else None

    async def handle(self, message: Any, next_handler: Callable[..., Awaitable[Any]]) -> Any:
        if self._counter:
            self._counter.inc()
        return await next_handler(message)
