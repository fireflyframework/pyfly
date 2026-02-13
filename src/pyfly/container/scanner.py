"""Package scanner for auto-discovering stereotype-decorated classes."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyfly.container.container import Container


def scan_package(package_name: str, container: Container) -> int:
    """Scan a package for stereotype-decorated classes and register them.

    Args:
        package_name: Dotted package name to scan (e.g. "myapp.services").
        container: Container to register discovered classes into.

    Returns:
        Number of classes registered.
    """
    count = 0
    module = importlib.import_module(package_name)

    # Register stereotype-decorated classes from this module
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


def scan_module_classes(module: object) -> list[type]:
    """Extract all stereotype-decorated classes from a module.

    Returns a list of classes that have ``__pyfly_injectable__ = True``.
    """
    classes: list[type] = []
    for _name, obj in inspect.getmembers(module, inspect.isclass):
        if getattr(obj, "__pyfly_injectable__", False) and obj.__module__ == module.__name__:
            classes.append(obj)
    return classes


def _register_from_module(module: object, container: Container) -> int:
    """Register all stereotype-decorated classes from a module."""
    from pyfly.container.types import Scope

    classes = scan_module_classes(module)
    for obj in classes:
        scope = getattr(obj, "__pyfly_scope__", None)
        condition = getattr(obj, "__pyfly_condition__", None)
        name = getattr(obj, "__pyfly_bean_name__", "")
        container.register(
            obj,
            scope=scope or Scope.SINGLETON,
            condition=condition,
            name=name,
        )
    return len(classes)
