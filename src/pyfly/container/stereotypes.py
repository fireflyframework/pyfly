"""Spring-style stereotype decorators for bean classification.

Each stereotype is an alias for container registration with semantic meaning:
- @component: generic managed bean
- @service: business logic layer
- @repository: data access layer
- @controller: web controller (template responses)
- @rest_controller: REST controller (JSON responses)
- @configuration: config class containing @bean methods
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, overload

from pyfly.container.types import Scope

T = TypeVar("T", bound=type)


def _make_stereotype(stereotype_name: str) -> Callable[..., Any]:
    """Factory that creates a stereotype decorator with the given name."""

    @overload
    def stereotype(cls: T) -> T: ...

    @overload
    def stereotype(
        *,
        name: str = "",
        scope: Scope = Scope.SINGLETON,
        profile: str = "",
        condition: Callable[..., bool] | None = None,
    ) -> Callable[[T], T]: ...

    def stereotype(
        cls: T | None = None,
        *,
        name: str = "",
        scope: Scope = Scope.SINGLETON,
        profile: str = "",
        condition: Callable[..., bool] | None = None,
    ) -> T | Callable[[T], T]:
        def decorator(cls: T) -> T:
            cls.__pyfly_injectable__ = True  # type: ignore[attr-defined]
            cls.__pyfly_stereotype__ = stereotype_name  # type: ignore[attr-defined]
            cls.__pyfly_scope__ = scope  # type: ignore[attr-defined]
            cls.__pyfly_condition__ = condition  # type: ignore[attr-defined]
            if name:
                cls.__pyfly_bean_name__ = name  # type: ignore[attr-defined]
            if profile:
                cls.__pyfly_profile__ = profile  # type: ignore[attr-defined]
            return cls

        if cls is not None:
            return decorator(cls)
        return decorator

    stereotype.__name__ = stereotype_name
    stereotype.__qualname__ = stereotype_name
    return stereotype


component = _make_stereotype("component")
service = _make_stereotype("service")
repository = _make_stereotype("repository")
controller = _make_stereotype("controller")
rest_controller = _make_stereotype("rest_controller")
configuration = _make_stereotype("configuration")
