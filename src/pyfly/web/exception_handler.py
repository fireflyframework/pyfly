"""Controller-level exception handler decorator."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

F = TypeVar("F", bound=Callable)


def exception_handler(exc_type: type[Exception]) -> Callable[[F], F]:
    """Mark a controller method as an exception handler.

    The handler is called when the specified exception type is raised
    by any handler in the same controller. Returns ``(status_code, body)``
    tuple or a Starlette Response.

    Usage::

        @exception_handler(OrderNotFoundException)
        async def handle_not_found(self, exc):
            return 404, {"error": "not found"}
    """

    def decorator(func: F) -> F:
        func.__pyfly_exception_handler__ = exc_type  # type: ignore[attr-defined]
        return func

    return decorator
