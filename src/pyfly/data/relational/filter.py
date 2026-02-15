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
"""Dynamic query building utilities for generating Specifications.

Provides :class:`FilterOperator` for individual column predicates and
:class:`FilterUtils` for auto-generating :class:`Specification` objects
from partial entities, dicts, or keyword arguments.  This is PyFly's
take on Spring Data's *Query by Example* pattern, but more Pythonic.

Example::

    # From keyword arguments (eq by default, ANDed together)
    spec = FilterUtils.by(name="Alice", active=True)
    results = await repo.find_all_by_spec(spec)

    # From a dict (None values are skipped)
    spec = FilterUtils.from_dict({"role": "admin", "name": None})

    # From a partial entity / dataclass
    spec = FilterUtils.from_example(UserFilter(role="admin"))

    # Using operators directly for richer predicates
    spec = FilterOperator.gte("age", 18) & FilterOperator.lt("age", 65)
"""

from __future__ import annotations

import dataclasses
from typing import Any, TypeVar

from pyfly.data.relational.specification import Specification

T = TypeVar("T")


class FilterOperator:
    """Filter operators for building dynamic specifications.

    Each static method returns a :class:`Specification` that applies a
    single column-level predicate.  Specifications can then be combined
    with ``&`` (AND), ``|`` (OR), and ``~`` (NOT).
    """

    @staticmethod
    def eq(field: str, value: Any) -> Specification[Any]:
        """Equal to."""
        return Specification(lambda root, q, _f=field, _v=value: q.where(getattr(root, _f) == _v))

    @staticmethod
    def neq(field: str, value: Any) -> Specification[Any]:
        """Not equal to."""
        return Specification(lambda root, q, _f=field, _v=value: q.where(getattr(root, _f) != _v))

    @staticmethod
    def gt(field: str, value: Any) -> Specification[Any]:
        """Greater than."""
        return Specification(lambda root, q, _f=field, _v=value: q.where(getattr(root, _f) > _v))

    @staticmethod
    def gte(field: str, value: Any) -> Specification[Any]:
        """Greater than or equal."""
        return Specification(
            lambda root, q, _f=field, _v=value: q.where(getattr(root, _f) >= _v)
        )

    @staticmethod
    def lt(field: str, value: Any) -> Specification[Any]:
        """Less than."""
        return Specification(lambda root, q, _f=field, _v=value: q.where(getattr(root, _f) < _v))

    @staticmethod
    def lte(field: str, value: Any) -> Specification[Any]:
        """Less than or equal."""
        return Specification(
            lambda root, q, _f=field, _v=value: q.where(getattr(root, _f) <= _v)
        )

    @staticmethod
    def like(field: str, pattern: str) -> Specification[Any]:
        """SQL LIKE pattern match."""
        return Specification(
            lambda root, q, _f=field, _p=pattern: q.where(getattr(root, _f).like(_p))
        )

    @staticmethod
    def contains(field: str, value: str) -> Specification[Any]:
        """String contains (wraps in ``%value%``)."""
        return Specification(
            lambda root, q, _f=field, _v=value: q.where(getattr(root, _f).contains(_v))
        )

    @staticmethod
    def in_list(field: str, values: list[Any]) -> Specification[Any]:
        """Value is in list."""
        return Specification(
            lambda root, q, _f=field, _v=values: q.where(getattr(root, _f).in_(_v))
        )

    @staticmethod
    def is_null(field: str) -> Specification[Any]:
        """Value is NULL."""
        return Specification(
            lambda root, q, _f=field: q.where(getattr(root, _f).is_(None))
        )

    @staticmethod
    def is_not_null(field: str) -> Specification[Any]:
        """Value is NOT NULL."""
        return Specification(
            lambda root, q, _f=field: q.where(getattr(root, _f).isnot(None))
        )

    @staticmethod
    def between(field: str, low: Any, high: Any) -> Specification[Any]:
        """Value is between *low* and *high* (inclusive)."""
        return Specification(
            lambda root, q, _f=field, _lo=low, _hi=high: q.where(
                getattr(root, _f).between(_lo, _hi)
            )
        )


class FilterUtils:
    """Generate Specifications dynamically from entities, dicts, or kwargs.

    This is PyFly's equivalent of Spring Data's *Query by Example*.

    Usage::

        # From keyword arguments (eq by default)
        spec = FilterUtils.by(name="Alice", active=True)

        # From a dict
        spec = FilterUtils.from_dict({"name": "Alice", "active": True})

        # From a partial entity (non-None fields become eq filters)
        spec = FilterUtils.from_example(User(name="Alice"))
    """

    @staticmethod
    def by(**kwargs: Any) -> Specification[Any]:
        """Create a specification from keyword arguments (all eq, ANDed)."""
        specs = [FilterOperator.eq(field, value) for field, value in kwargs.items()]
        return FilterUtils._combine_and(specs)

    @staticmethod
    def from_dict(filters: dict[str, Any]) -> Specification[Any]:
        """Create a specification from a dict of field->value pairs (all eq, ANDed).

        ``None`` values are skipped.
        """
        specs = [
            FilterOperator.eq(field, value)
            for field, value in filters.items()
            if value is not None
        ]
        return FilterUtils._combine_and(specs)

    @staticmethod
    def from_example(example: Any) -> Specification[Any]:
        """Create a specification from an example entity/DTO.

        Extracts non-``None`` field values and creates eq filters for each.
        Supports dataclasses and any object with ``__dict__``.
        """
        if dataclasses.is_dataclass(example) and not isinstance(example, type):
            fields = {
                f.name: getattr(example, f.name)
                for f in dataclasses.fields(example)
            }
        else:
            fields = vars(example)

        specs = [
            FilterOperator.eq(field, value)
            for field, value in fields.items()
            if value is not None
        ]
        return FilterUtils._combine_and(specs)

    @staticmethod
    def _combine_and(specs: list[Specification[Any]]) -> Specification[Any]:
        """AND-combine a list of specs.  Returns a no-op if empty."""
        if not specs:
            return Specification(lambda root, q: q)
        result = specs[0]
        for s in specs[1:]:
            result = result & s
        return result
