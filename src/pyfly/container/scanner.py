"""Package scanner for auto-discovering @injectable classes."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyfly.container.container import Container


def scan_package(package_name: str, container: Container) -> int:
    """Scan a package for @injectable classes and register them.

    Args:
        package_name: Dotted package name to scan (e.g. "myapp.services").
        container: Container to register discovered classes into.

    Returns:
        Number of classes registered.
    """
    count = 0
    module = importlib.import_module(package_name)

    # Register injectables from this module
    count += _register_from_module(module, container)

    # If it's a package, scan submodules
    if hasattr(module, "__path__"):
        for _importer, modname, _ispkg in pkgutil.walk_packages(
            module.__path__, prefix=module.__name__ + "."
        ):
            try:
                submodule = importlib.import_module(modname)
                count += _register_from_module(submodule, container)
            except ImportError:
                continue

    return count


def _register_from_module(module: object, container: Container) -> int:
    """Register all @injectable classes from a module."""
    from pyfly.container.types import Scope

    count = 0
    for _name, obj in inspect.getmembers(module, inspect.isclass):
        if getattr(obj, "__pyfly_injectable__", False) and obj.__module__ == module.__name__:
            scope = getattr(obj, "__pyfly_scope__", None)
            condition = getattr(obj, "__pyfly_condition__", None)
            container.register(
                obj,
                scope=scope or Scope.SINGLETON,
                condition=condition,
            )
            count += 1
    return count
