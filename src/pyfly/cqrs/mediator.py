"""CQRS Mediator — routes commands and queries to their handlers."""

from __future__ import annotations

from typing import Any

from pyfly.cqrs.types import Command, CommandHandler, Query, QueryHandler


class Mediator:
    """Routes commands and queries to registered handlers.

    Handlers are discovered via the DI container or registered manually.
    Each command/query type maps to exactly one handler.
    """

    def __init__(self) -> None:
        self._handlers: dict[type, CommandHandler | QueryHandler] = {}  # type: ignore[type-arg]

    def register_handler(
        self,
        message_type: type[Command] | type[Query],
        handler: CommandHandler | QueryHandler,  # type: ignore[type-arg]
    ) -> None:
        """Register a handler for a command or query type."""
        self._handlers[message_type] = handler

    async def send(self, message: Command | Query) -> Any:
        """Dispatch a command or query to its handler."""
        message_type = type(message)
        handler = self._handlers.get(message_type)
        if handler is None:
            raise KeyError(f"No handler registered for {message_type.__name__}")
        return await handler.handle(message)  # type: ignore[arg-type]
