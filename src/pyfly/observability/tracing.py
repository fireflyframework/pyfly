"""Distributed tracing with OpenTelemetry span decorator."""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, TypeVar

from opentelemetry import trace

F = TypeVar("F", bound=Callable[..., Any])

_tracer = trace.get_tracer("pyfly")


def span(name: str) -> Callable[[F], F]:
    """Decorator that wraps an async function in an OpenTelemetry span.

    Usage:
        @span("process-order")
        async def process_order(order_id: str) -> dict: ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            with _tracer.start_as_current_span(name) as current_span:
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as exc:
                    current_span.set_status(
                        trace.Status(trace.StatusCode.ERROR, str(exc))
                    )
                    current_span.record_exception(exc)
                    raise

        return wrapper  # type: ignore[return-value]

    return decorator
