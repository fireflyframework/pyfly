"""Application bootstrap — the entry point for PyFly applications."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, TypeVar

from pyfly.container import Container
from pyfly.container.scanner import scan_package
from pyfly.container.types import Scope
from pyfly.core.config import Config

T = TypeVar("T")

logger = logging.getLogger("pyfly.core")


def pyfly_application(
    name: str,
    version: str = "0.1.0",
    scan_packages: list[str] | None = None,
    description: str = "",
) -> Any:
    """Decorator marking a class as a PyFly application entry point.

    Args:
        name: Application name (used in config, logging, metrics).
        version: Application version.
        scan_packages: Packages to scan for @injectable classes.
        description: Human-readable description.
    """

    def decorator(cls: type[T]) -> type[T]:
        cls.__pyfly_app_name__ = name  # type: ignore[attr-defined]
        cls.__pyfly_app_version__ = version  # type: ignore[attr-defined]
        cls.__pyfly_scan_packages__ = scan_packages or []  # type: ignore[attr-defined]
        cls.__pyfly_app_description__ = description  # type: ignore[attr-defined]
        return cls

    return decorator


class PyFlyApplication:
    """Main application class that bootstraps the framework.

    Initializes the DI container, loads configuration, scans for
    injectable classes, and manages the application lifecycle.
    """

    def __init__(self, app_class: type, config_path: str | Path | None = None) -> None:
        self._app_class = app_class
        self._name: str = getattr(app_class, "__pyfly_app_name__", "pyfly-app")
        self._version: str = getattr(app_class, "__pyfly_app_version__", "0.1.0")
        self._scan_packages: list[str] = getattr(app_class, "__pyfly_scan_packages__", [])

        # Load configuration
        if config_path:
            self.config = Config.from_file(config_path)
        else:
            # Try default locations
            for candidate in ["pyfly.yaml", "pyfly.toml", "config/pyfly.yaml"]:
                if Path(candidate).exists():
                    self.config = Config.from_file(candidate)
                    break
            else:
                self.config = Config({})

        # Create DI container
        self.container = Container()

        # Register the config itself
        self.container.register(Config, scope=Scope.SINGLETON)
        self.container._registrations[Config].instance = self.config

        # Auto-discover injectable classes
        for package in self._scan_packages:
            try:
                count = scan_package(package, self.container)
                logger.info("Scanned %s: found %d injectable classes", package, count)
            except ImportError as e:
                logger.warning("Could not scan package %s: %s", package, e)

    async def startup(self) -> None:
        """Start the application — call lifecycle hooks."""
        logger.info("Starting %s v%s", self._name, self._version)
        await self.container.startup()

    async def shutdown(self) -> None:
        """Shutdown the application — call lifecycle hooks."""
        logger.info("Shutting down %s", self._name)
        await self.container.shutdown()
