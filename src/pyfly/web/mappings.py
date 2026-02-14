"""HTTP method mapping decorators for class-based controllers.

Mirrors Spring Boot's @RequestMapping, @GetMapping, @PostMapping, etc.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T", bound=type)
F = TypeVar("F", bound=Callable[..., Any])


def request_mapping(path: str) -> Callable[[T], T]:
    """Class-level decorator that sets the base path for all handler methods."""

    def decorator(cls: T) -> T:
        cls.__pyfly_request_mapping__ = path.rstrip("/")  # type: ignore[attr-defined]
        return cls

    return decorator


def _make_method_mapping(method: str) -> Callable[..., Any]:
    """Factory that creates an HTTP method mapping decorator."""

    def mapping(path: str = "", *, status_code: int = 200) -> Callable[[F], F]:
        def decorator(func: F) -> F:
            func.__pyfly_mapping__ = {  # type: ignore[attr-defined]
                "method": method,
                "path": path,
                "status_code": status_code,
            }
            return func

        return decorator

    mapping.__name__ = f"{method.lower()}_mapping"
    mapping.__qualname__ = f"{method.lower()}_mapping"
    return mapping


get_mapping = _make_method_mapping("GET")
post_mapping = _make_method_mapping("POST")
put_mapping = _make_method_mapping("PUT")
patch_mapping = _make_method_mapping("PATCH")
delete_mapping = _make_method_mapping("DELETE")
