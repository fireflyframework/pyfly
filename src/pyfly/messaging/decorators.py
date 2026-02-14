"""Decorators for declarative message handling."""
from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def message_listener(topic: str, group: str | None = None) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        wrapper.__pyfly_message_listener__ = True  # type: ignore[attr-defined]
        wrapper.__pyfly_listener_topic__ = topic  # type: ignore[attr-defined]
        wrapper.__pyfly_listener_group__ = group  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorator
