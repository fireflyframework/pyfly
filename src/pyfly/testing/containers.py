"""Test container factory for integration testing."""

from __future__ import annotations

from typing import Any

from pyfly.container import Container, Scope


def create_test_container(
    overrides: dict[type, type] | None = None,
) -> Container:
    """Create a pre-configured Container for testing.

    Registers any override mappings (interface -> test implementation)
    so tests can substitute real services with fakes/mocks.

    Args:
        overrides: Mapping of interface types to test implementations.

    Returns:
        A configured Container ready for testing.
    """
    container = Container()

    if overrides:
        for interface, impl in overrides.items():
            container.register(impl, scope=Scope.SINGLETON)
            if interface != impl:
                container.bind(interface, impl)

    return container
