"""Lightweight DI container with type-hint based resolution."""

from __future__ import annotations

import typing
from typing import Any, TypeVar

from pyfly.container.registry import Registration
from pyfly.container.types import Scope

T = TypeVar("T")


class Container:
    """Dependency injection container.

    Supports constructor injection via type hints, scoped lifecycles,
    and interface-to-implementation binding.
    """

    def __init__(self) -> None:
        self._registrations: dict[type, Registration] = {}
        self._bindings: dict[type, type] = {}

    def register(
        self,
        cls: type,
        scope: Scope = Scope.SINGLETON,
        condition: Any = None,
    ) -> None:
        """Register a class for injection."""
        self._registrations[cls] = Registration(
            impl_type=cls,
            scope=scope,
            condition=condition,
        )

    def bind(self, interface: type, implementation: type) -> None:
        """Bind an interface/base class to a concrete implementation."""
        self._bindings[interface] = implementation

    def resolve(self, cls: type[T]) -> T:
        """Resolve an instance of the given type."""
        # Follow binding if interface
        target = self._bindings.get(cls, cls)

        if target not in self._registrations:
            raise KeyError(f"No registration found for {target.__name__}")

        reg = self._registrations[target]

        # Return cached singleton
        if reg.scope == Scope.SINGLETON and reg.instance is not None:
            return reg.instance  # type: ignore[return-value]

        # Build instance with constructor injection
        instance = self._create_instance(reg)

        # Cache singletons
        if reg.scope == Scope.SINGLETON:
            reg.instance = instance

        return instance  # type: ignore[return-value]

    def _create_instance(self, reg: Registration) -> Any:
        """Create an instance, resolving constructor dependencies."""
        init = reg.impl_type.__init__
        if init is object.__init__:
            return reg.impl_type()

        hints = typing.get_type_hints(init)
        hints.pop("return", None)

        kwargs: dict[str, Any] = {}
        for param_name, param_type in hints.items():
            kwargs[param_name] = self.resolve(param_type)

        return reg.impl_type(**kwargs)
