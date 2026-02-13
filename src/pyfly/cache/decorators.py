"""Declarative caching decorators."""

from __future__ import annotations

import functools
import inspect
import json
from datetime import timedelta
from typing import Any, Callable, TypeVar

from pyfly.cache.types import CacheAdapter

F = TypeVar("F", bound=Callable[..., Any])


def cache(
    backend: CacheAdapter,
    key: str,
    ttl: timedelta | None = None,
) -> Callable[[F], F]:
    """Cache the return value of an async function.

    The `key` parameter supports format-string interpolation with function
    argument names. For example, `key="user:{user_id}"` will expand
    `{user_id}` from the function's arguments.

    Args:
        backend: Cache adapter to use.
        key: Key template with {param} placeholders.
        ttl: Optional time-to-live for cached entries.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Resolve the cache key from function arguments
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            resolved_key = key.format(**bound.arguments)

            # Check cache
            cached = await backend.get(resolved_key)
            if cached is not None:
                return cached

            # Execute and cache
            result = await func(*args, **kwargs)
            await backend.put(resolved_key, result, ttl=ttl)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator
