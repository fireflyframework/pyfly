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
"""Infer :class:`ShellParam` descriptors from a callable's type hints."""

from __future__ import annotations

import inspect
import types
import typing
from typing import Any, Callable, Union, get_type_hints

from pyfly.shell.result import ShellParam, _MISSING

_SKIP = frozenset({"self", "return"})


def _unwrap_optional(tp: Any) -> tuple[Any, bool]:
    """Unwrap ``Optional[T]``, ``Union[T, None]``, and ``T | None`` (PEP 604).

    Returns a ``(inner_type, was_optional)`` tuple.  If *tp* is not an
    optional wrapper the original type is returned unchanged.
    """
    origin = typing.get_origin(tp)

    # PEP 604 – ``T | None`` surfaces as ``types.UnionType`` on 3.10+.
    if isinstance(tp, types.UnionType):
        args = typing.get_args(tp)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and len(args) == 2:
            return non_none[0], True
        return tp, False

    # ``typing.Optional[T]`` / ``Union[T, None]``
    if origin is Union:
        args = typing.get_args(tp)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and len(args) == 2:
            return non_none[0], True

    return tp, False


def infer_params(func: Callable[..., Any]) -> list[ShellParam]:
    """Build a list of :class:`ShellParam` from *func*'s signature and type hints."""
    sig = inspect.signature(func)
    try:
        hints = get_type_hints(func)
    except Exception:  # pragma: no cover – defensive for unresolvable hints
        hints = {}

    params: list[ShellParam] = []

    for name, p in sig.parameters.items():
        if name in _SKIP:
            continue

        raw_type = hints.get(name, str)
        inner_type, was_optional = _unwrap_optional(raw_type)
        has_default = p.default is not inspect.Parameter.empty

        # Determine default value
        if has_default:
            default: Any = p.default
        elif was_optional:
            default = None
        else:
            default = _MISSING

        # bool → flag option
        if inner_type is bool:
            params.append(
                ShellParam(
                    name=name,
                    param_type=bool,
                    is_option=True,
                    default=default if default is not _MISSING else False,
                    is_flag=True,
                )
            )
            continue

        # Has a default or is optional → option
        is_option = has_default or was_optional

        params.append(
            ShellParam(
                name=name,
                param_type=inner_type,
                is_option=is_option,
                default=default,
            )
        )

    return params
