# Copyright 2026 Firefly Software Solutions Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
