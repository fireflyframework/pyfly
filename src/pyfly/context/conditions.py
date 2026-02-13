"""Conditional bean decorators — control when beans are registered."""

from __future__ import annotations

import importlib
from typing import Any, TypeVar

T = TypeVar("T", bound=type)


def conditional_on_property(key: str, having_value: str = "") -> Any:
    """Only register this bean if the given config property matches.

    Evaluated at ApplicationContext startup against the active Environment.
    """

    def decorator(cls: T) -> T:
        conditions = getattr(cls, "__pyfly_conditions__", [])
        conditions.append({
            "type": "on_property",
            "key": key,
            "having_value": having_value,
        })
        cls.__pyfly_conditions__ = conditions  # type: ignore[attr-defined]
        return cls

    return decorator


def conditional_on_class(module_name: str) -> Any:
    """Only register this bean if the given module is importable.

    Mirrors Spring Boot's @ConditionalOnClass.
    """

    def _check() -> bool:
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False

    def decorator(cls: T) -> T:
        conditions = getattr(cls, "__pyfly_conditions__", [])
        conditions.append({
            "type": "on_class",
            "module_name": module_name,
            "check": _check,
        })
        cls.__pyfly_conditions__ = conditions  # type: ignore[attr-defined]
        return cls

    return decorator


def conditional_on_missing_bean(bean_type: type) -> Any:
    """Only register this bean if no other bean of the given type exists.

    Evaluated at ApplicationContext startup after initial registration.
    """

    def decorator(cls: T) -> T:
        conditions = getattr(cls, "__pyfly_conditions__", [])
        conditions.append({
            "type": "on_missing_bean",
            "bean_type": bean_type,
        })
        cls.__pyfly_conditions__ = conditions  # type: ignore[attr-defined]
        return cls

    return decorator
