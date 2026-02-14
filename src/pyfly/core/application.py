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
"""Application bootstrap — the entry point for PyFly applications."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from pyfly.container.scanner import scan_package
from pyfly.core.banner import BannerPrinter
from pyfly.core.config import Config
from pyfly.logging.structlog_adapter import StructlogAdapter

if TYPE_CHECKING:
    from pyfly.context.application_context import ApplicationContext

T = TypeVar("T")


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

    Startup sequence (Spring Boot parity):
    1. Configure logging (from pyfly.yaml logging section)
    2. Print banner (respecting pyfly.banner.mode)
    3. Log "Starting {app} v{version}"
    4. Log "Active profiles: {profiles}" or "No active profiles set"
    5. Load profile-specific config files
    6. Filter beans by active profiles
    7. Sort beans by @order value
    8. Initialize beans (respecting order)
    9. Log "Started {app} in {time}s ({count} beans initialized)"
    """

    def __init__(self, app_class: type, config_path: str | Path | None = None) -> None:
        self._app_class = app_class
        self._name: str = getattr(app_class, "__pyfly_app_name__", "pyfly-app")
        self._version: str = getattr(app_class, "__pyfly_app_version__", "0.1.0")
        self._scan_packages: list[str] = getattr(app_class, "__pyfly_scan_packages__", [])
        self._startup_time: float = 0.0

        # 1. Load configuration (with profile merging)
        config_file = self._find_config(config_path)
        active_profiles = self._resolve_profiles_early(config_file)
        if config_file:
            self.config = Config.from_file(config_file, active_profiles=active_profiles)
        else:
            self.config = Config({})

        # 2. Configure logging
        self._logging = StructlogAdapter()
        self._logging.configure(self.config)
        self._logger = self._logging.get_logger("pyfly.core")

        # Deferred import to avoid circular import
        from pyfly.context.application_context import ApplicationContext

        # Create ApplicationContext
        self._context = ApplicationContext(self.config)

        # Auto-discover beans from scanned packages
        for package in self._scan_packages:
            try:
                count = scan_package(package, self._context.container)
                self._logger.info("scanned_package", package=package, beans_found=count)
            except ImportError as e:
                self._logger.warning("scan_failed", package=package, error=str(e))

    @property
    def context(self) -> ApplicationContext:
        """The ApplicationContext."""
        return self._context

    @property
    def startup_time_seconds(self) -> float:
        """Time taken to start the application, in seconds."""
        return self._startup_time

    async def startup(self) -> None:
        """Start the application with full Spring Boot-style startup sequence."""
        start = time.perf_counter()

        # Print banner
        profiles = self._context.environment.active_profiles
        banner = BannerPrinter.from_config(
            self.config,
            version=self._version,
            app_name=self._name,
            app_version=self._version,
            active_profiles=profiles,
        )
        banner_text = banner.render()
        if banner_text:
            print(banner_text)  # noqa: T201
            sys.stdout.flush()

        # Log startup info
        self._logger.info("starting_application", app=self._name, version=self._version)

        if profiles:
            self._logger.info("active_profiles", profiles=profiles)
        else:
            self._logger.info("no_active_profiles", message="No active profiles set, falling back to default")

        # Start the context (handles profile filtering, @order sorting, bean init)
        await self._context.start()

        self._startup_time = time.perf_counter() - start

        self._logger.info(
            "application_started",
            app=self._name,
            startup_time_s=round(self._startup_time, 3),
            beans_initialized=self._context.bean_count,
        )

    async def shutdown(self) -> None:
        """Shutdown the application — stop the ApplicationContext."""
        self._logger.info("shutting_down", app=self._name)
        await self._context.stop()

    def _find_config(self, config_path: str | Path | None) -> Path | None:
        """Find the configuration file path."""
        if config_path:
            return Path(config_path)
        for candidate in ["pyfly.yaml", "pyfly.toml", "config/pyfly.yaml"]:
            if Path(candidate).exists():
                return Path(candidate)
        return None

    @staticmethod
    def _resolve_profiles_early(config_path: Path | None) -> list[str]:
        """Resolve active profiles before full config load (for merging)."""
        import os

        import yaml

        # Env var takes priority
        env_profiles = os.environ.get("PYFLY_PROFILES_ACTIVE", "")
        if env_profiles:
            return [p.strip() for p in env_profiles.split(",") if p.strip()]

        # Read from base config file
        if config_path and config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}
            profiles_value = (data.get("pyfly", {}) or {}).get("profiles", {})
            active = profiles_value.get("active", "") if isinstance(profiles_value, dict) else ""
            if active:
                return [p.strip() for p in str(active).split(",") if p.strip()]

        return []
