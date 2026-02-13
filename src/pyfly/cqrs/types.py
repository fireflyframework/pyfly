"""CQRS base types."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Command:
    """Base class for commands (write operations)."""


class Query:
    """Base class for queries (read operations)."""


class CommandHandler(Generic[T]):
    """Base class for command handlers."""

    async def handle(self, command: T) -> Any:
        raise NotImplementedError


class QueryHandler(Generic[T]):
    """Base class for query handlers."""

    async def handle(self, query: T) -> Any:
        raise NotImplementedError
