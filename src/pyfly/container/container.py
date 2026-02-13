"""Lightweight DI container with type-hint based resolution."""

from __future__ import annotations

import typing
from typing import Annotated, Any, TypeVar, get_args, get_origin

from pyfly.container.bean import Qualifier
from pyfly.container.registry import Registration
from pyfly.container.types import Scope

T = TypeVar("T")


class Container:
    """Dependency injection container.

    Supports constructor injection via type hints, scoped lifecycles,
    interface-to-implementation binding, named beans, @primary resolution,
    and Qualifier-based disambiguation.
    """

    def __init__(self) -> None:
        self._registrations: dict[type, Registration] = {}
        self._named: dict[str, Registration] = {}
        self._bindings: dict[type, list[type]] = {}

    def register(
        self,
        cls: type,
        scope: Scope = Scope.SINGLETON,
        condition: Any = None,
        name: str = "",
    ) -> None:
        """Register a class for injection."""
        bean_name = name or getattr(cls, "__pyfly_bean_name__", "")
        bean_scope = getattr(cls, "__pyfly_scope__", None) or scope
        reg = Registration(
            impl_type=cls,
            scope=bean_scope,
            condition=condition,
            name=bean_name,
        )
        self._registrations[cls] = reg
        if bean_name:
            self._named[bean_name] = reg

    def bind(self, interface: type, implementation: type) -> None:
        """Bind an interface/base class to a concrete implementation."""
        if interface not in self._bindings:
            self._bindings[interface] = []
        if implementation not in self._bindings[interface]:
            self._bindings[interface].append(implementation)

    def resolve(self, cls: type[T]) -> T:
        """Resolve an instance of the given type."""
        # Direct registration
        if cls in self._registrations:
            return self._resolve_registration(self._registrations[cls])

        # Follow binding(s)
        impls = self._bindings.get(cls, [])
        if not impls:
            raise KeyError(f"No registration found for {cls.__name__}")

        if len(impls) == 1:
            return self._resolve_registration(self._registrations[impls[0]])

        # Multiple impls: pick @primary
        for impl in impls:
            if getattr(impl, "__pyfly_primary__", False):
                return self._resolve_registration(self._registrations[impl])

        raise KeyError(
            f"Multiple implementations for {cls.__name__} but none marked @primary: "
            f"{[i.__name__ for i in impls]}"
        )

    def resolve_by_name(self, name: str) -> Any:
        """Resolve a bean by its registered name."""
        if name not in self._named:
            raise KeyError(f"No bean named '{name}'")
        return self._resolve_registration(self._named[name])

    def resolve_all(self, cls: type[T]) -> list[T]:
        """Resolve all implementations bound to an interface."""
        impls = self._bindings.get(cls, [])
        return [self._resolve_registration(self._registrations[impl]) for impl in impls]

    def contains(self, name: str) -> bool:
        """Check if a named bean exists."""
        return name in self._named

    def _resolve_registration(self, reg: Registration) -> Any:
        """Resolve a single registration, handling scope."""
        if reg.scope == Scope.SINGLETON and reg.instance is not None:
            return reg.instance

        instance = self._create_instance(reg)

        if reg.scope == Scope.SINGLETON:
            reg.instance = instance

        return instance

    def _create_instance(self, reg: Registration) -> Any:
        """Create an instance, resolving constructor dependencies."""
        init = reg.impl_type.__init__
        if init is object.__init__:
            return reg.impl_type()

        hints = typing.get_type_hints(init, include_extras=True)
        hints.pop("return", None)

        kwargs: dict[str, Any] = {}
        for param_name, param_type in hints.items():
            kwargs[param_name] = self._resolve_param(param_type)

        return reg.impl_type(**kwargs)

    def _resolve_param(self, param_type: type) -> Any:
        """Resolve a single constructor parameter, handling Annotated[T, Qualifier]."""
        if get_origin(param_type) is Annotated:
            args = get_args(param_type)
            base_type = args[0]
            for metadata in args[1:]:
                if isinstance(metadata, Qualifier):
                    return self.resolve_by_name(metadata.name)
            return self.resolve(base_type)
        return self.resolve(param_type)

    async def startup(self) -> None:
        """Call on_init on all resolved singleton instances."""
        from pyfly.container.lifecycle import call_lifecycle_hook

        for reg in self._registrations.values():
            if reg.instance is not None:
                await call_lifecycle_hook(reg.instance, "on_init")

    async def shutdown(self) -> None:
        """Call on_destroy on all resolved singleton instances (reverse order)."""
        from pyfly.container.lifecycle import call_lifecycle_hook

        instances = [
            reg.instance
            for reg in reversed(list(self._registrations.values()))
            if reg.instance is not None
        ]
        for instance in instances:
            await call_lifecycle_hook(instance, "on_destroy")
