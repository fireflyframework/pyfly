"""Bean initialization ordering — @order decorator and precedence constants."""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T", bound=type)

HIGHEST_PRECEDENCE: int = -(2**31)
LOWEST_PRECEDENCE: int = 2**31 - 1


def order(value: int) -> callable:
    """Set the initialization order for a bean class.

    Lower value = higher priority (initialized first).
    Default order for undecorated beans is 0.
    """

    def decorator(cls: T) -> T:
        cls.__pyfly_order__ = value  # type: ignore[attr-defined]
        return cls

    return decorator


def get_order(cls: type) -> int:
    """Get the order value for a class, defaulting to 0."""
    return getattr(cls, "__pyfly_order__", 0)
