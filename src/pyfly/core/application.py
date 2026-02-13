"""Application bootstrap — the entry point for PyFly applications."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from pyfly.container.scanner import scan_package
from pyfly.core.config import Config

if TYPE_CHECKING:
    from pyfly.context.application_context import ApplicationContext

T = TypeVar("T")

logger = logging.getLogger("pyfly.core")


def pyfly_application(
    name: str,
    version: str = "0.1.0",
    scan_packages: list[str] | None = None,
    description: str = "",
) -> Any:
    """Decorator marking a class as a PyFly application entry point."""

    def decorator(cls: type[T]) -> type[T]:
        cls.__pyfly_app_name__ = name  # type: ignore[attr-defined]
        cls.__pyfly_app_version__ = version  # type: ignore[attr-defined]
        cls.__pyfly_scan_packages__ = scan_packages or []  # type: ignore[attr-defined]
        cls.__pyfly_app_description__ = description  # type: ignore[attr-defined]
        return cls

    return decorator


class PyFlyApplication:
    """Main application class that bootstraps the framework.

    Creates an ApplicationContext, loads configuration, scans for
    beans, and manages the application lifecycle.
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
            for candidate in ["pyfly.yaml", "pyfly.toml", "config/pyfly.yaml"]:
                if Path(candidate).exists():
                    self.config = Config.from_file(candidate)
                    break
            else:
                self.config = Config({})

        # Deferred import to avoid circular import
        # (core.__init__ -> application -> context -> environment -> core.config -> core.__init__)
        from pyfly.context.application_context import ApplicationContext

        # Create ApplicationContext (wraps Container)
        self._context = ApplicationContext(self.config)

        # Auto-discover beans from scanned packages
        for package in self._scan_packages:
            try:
                count = scan_package(package, self._context.container)
                logger.info("Scanned %s: found %d beans", package, count)
            except ImportError as e:
                logger.warning("Could not scan package %s: %s", package, e)

    @property
    def context(self) -> ApplicationContext:
        """The ApplicationContext."""
        return self._context

    async def startup(self) -> None:
        """Start the application — start the ApplicationContext."""
        logger.info("Starting %s v%s", self._name, self._version)
        await self._context.start()

    async def shutdown(self) -> None:
        """Shutdown the application — stop the ApplicationContext."""
        logger.info("Shutting down %s", self._name)
        await self._context.stop()
