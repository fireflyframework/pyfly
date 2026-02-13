"""Decorators for declarative event publishing and consumption."""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, TypeVar

from pyfly.eda.memory import InMemoryEventBus
from pyfly.eda.types import EventEnvelope

F = TypeVar("F", bound=Callable[..., Any])


def event_publisher(
    bus: InMemoryEventBus,
    destination: str,
    event_type: str,
    timing: str = "BEFORE",
) -> Callable[[F], F]:
    """Publish method arguments as events.

    Args:
        bus: Event bus instance.
        destination: Topic/queue name.
        event_type: Event type identifier.
        timing: When to publish — BEFORE, AFTER, or BOTH.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Build payload from args
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            payload = _serialize_payload(dict(bound.arguments))

            if timing in ("BEFORE", "BOTH"):
                await bus.publish(destination, event_type, payload)

            result = await func(*args, **kwargs)

            if timing in ("AFTER", "BOTH"):
                await bus.publish(destination, event_type, payload)

            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def publish_result(
    bus: InMemoryEventBus,
    destination: str,
    event_type: str,
    condition: Callable[..., bool] | None = None,
) -> Callable[[F], F]:
    """Publish method return value as an event.

    Args:
        bus: Event bus instance.
        destination: Topic/queue name.
        event_type: Event type identifier.
        condition: Optional predicate on the result — publish only if True.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)

            should_publish = condition(result) if condition else True
            if should_publish:
                payload = result if isinstance(result, dict) else {"result": result}
                await bus.publish(destination, event_type, payload)

            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def event_listener(
    bus: InMemoryEventBus,
    event_types: list[str],
) -> Callable[[F], F]:
    """Register a function as an event listener.

    Args:
        bus: Event bus instance.
        event_types: List of event type patterns to subscribe to.
    """

    def decorator(func: F) -> F:
        for pattern in event_types:
            bus.subscribe(pattern, func)
        return func

    return decorator


def _serialize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Convert payload values to JSON-serializable types."""
    result: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            result[key] = value
        elif hasattr(value, "__dict__"):
            result[key] = value.__dict__
        else:
            result[key] = value
    return result
