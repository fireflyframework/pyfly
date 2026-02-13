"""Decorators for dependency injection."""

from __future__ import annotations

from typing import Callable, TypeVar, overload

from pyfly.container.types import Scope

T = TypeVar("T", bound=type)


@overload
def injectable(cls: T) -> T: ...


@overload
def injectable(
    *,
    scope: Scope = Scope.SINGLETON,
    condition: Callable[..., bool] | None = None,
) -> Callable[[T], T]: ...


def injectable(
    cls: T | None = None,
    *,
    scope: Scope = Scope.SINGLETON,
    condition: Callable[..., bool] | None = None,
) -> T | Callable[[T], T]:
    """Mark a class as injectable into the DI container.

    Can be used with or without arguments:
        @injectable
        class MyService: ...

        @injectable(scope=Scope.TRANSIENT)
        class MyService: ...
    """

    def decorator(cls: T) -> T:
        cls.__pyfly_injectable__ = True  # type: ignore[attr-defined]
        cls.__pyfly_scope__ = scope  # type: ignore[attr-defined]
        cls.__pyfly_condition__ = condition  # type: ignore[attr-defined]
        return cls

    if cls is not None:
        return decorator(cls)
    return decorator
