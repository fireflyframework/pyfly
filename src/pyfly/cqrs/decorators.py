"""CQRS handler decorators."""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T", bound=type)


def command_handler(cls: T) -> T:
    """Mark a class as a command handler for auto-discovery."""
    cls.__pyfly_handler_type__ = "command"  # type: ignore[attr-defined]
    return cls


def query_handler(cls: T) -> T:
    """Mark a class as a query handler for auto-discovery."""
    cls.__pyfly_handler_type__ = "query"  # type: ignore[attr-defined]
    return cls
