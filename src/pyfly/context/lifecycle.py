"""Lifecycle annotations: @post_construct and @pre_destroy."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

F = TypeVar("F", bound=Callable)


def post_construct(func: F) -> F:
    """Mark a method to be called after the bean is fully initialized.

    Replaces the magic ``on_init`` method name convention.
    """
    func.__pyfly_post_construct__ = True  # type: ignore[attr-defined]
    return func


def pre_destroy(func: F) -> F:
    """Mark a method to be called before the bean is destroyed.

    Replaces the magic ``on_destroy`` method name convention.
    """
    func.__pyfly_pre_destroy__ = True  # type: ignore[attr-defined]
    return func
