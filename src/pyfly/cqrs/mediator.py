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
"""CQRS Mediator — routes commands and queries to their handlers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from pyfly.cqrs.types import Command, CommandHandler, Query, QueryHandler


class Mediator:
    """Routes commands and queries to registered handlers.

    Supports an optional middleware pipeline that wraps handler execution.
    Each command/query type maps to exactly one handler.
    """

    def __init__(self, middleware: list[Any] | None = None) -> None:
        self._handlers: dict[type, CommandHandler | QueryHandler] = {}  # type: ignore[type-arg]
        self._middleware = middleware or []

    def register_handler(
        self,
        message_type: type[Command] | type[Query],
        handler: CommandHandler | QueryHandler,  # type: ignore[type-arg]
    ) -> None:
        """Register a handler for a command or query type."""
        self._handlers[message_type] = handler

    async def send(self, message: Command | Query) -> Any:
        """Dispatch a command or query through the middleware pipeline to its handler."""
        message_type = type(message)
        handler = self._handlers.get(message_type)
        if handler is None:
            raise KeyError(f"No handler registered for {message_type.__name__}")

        async def invoke(msg: Command | Query) -> Any:
            return await handler.handle(msg)  # type: ignore[arg-type]

        # Build the middleware chain (innermost = handler)
        chain: Callable[..., Awaitable[Any]] = invoke
        for mw in reversed(self._middleware):
            chain = _wrap(mw, chain)

        return await chain(message)


def _wrap(
    middleware: Any,
    next_handler: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    """Create a closure that calls middleware.handle with the next handler.

    Extracted as a standalone function to avoid Python late-binding issues
    in a loop.
    """

    async def _next(msg: Command | Query) -> Any:
        return await middleware.handle(msg, next_handler)

    return _next
