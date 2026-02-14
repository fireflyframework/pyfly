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

from pyfly.container.exceptions import BeanCreationException
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

        # 1. Load configuration (with profile merging, multi-source)
        config_dir = self._find_config_dir(config_path)
        active_profiles = self._resolve_profiles_early(config_dir)
        if config_dir:
            self.config = Config.from_sources(config_dir, active_profiles=active_profiles)
        else:
            self.config = Config(Config._load_framework_defaults())
            self.config._loaded_sources = ["pyfly-defaults.yaml (framework defaults)"]

        # 2. Configure logging
        self._logging = StructlogAdapter()
        self._logging.configure(self.config)
        self._logger = self._logging.get_logger("pyfly.core")

        # Deferred import to avoid circular import
        from pyfly.context.application_context import ApplicationContext

        # Create ApplicationContext
        self._context = ApplicationContext(self.config)

        # Auto-discover beans from scanned packages (logging deferred to startup)
        self._scan_results: list[tuple[str, int]] = []
        for package in self._scan_packages:
            try:
                count = scan_package(package, self._context.container)
                self._scan_results.append((package, count))
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

        # Log loaded config sources
        for source in self.config.loaded_sources:
            self._logger.info("loaded_config", source=source)

        # Log deferred scan results (now appears after banner)
        for package, count in self._scan_results:
            self._logger.info("scanned_package", package=package, beans_found=count)

        # Start the context (handles profile filtering, @order sorting, bean init)
        try:
            await self._context.start()
        except BeanCreationException as exc:
            self._logger.error(
                "application_failed",
                app=self._name,
                error=str(exc),
                subsystem=exc.subsystem,
                provider=exc.provider,
            )
            raise

        self._startup_time = time.perf_counter() - start

        self._logger.info(
            "application_started",
            app=self._name,
            startup_time_s=round(self._startup_time, 3),
            beans_initialized=self._context.bean_count,
        )

        # Log routes and API documentation URLs
        self._log_routes_and_docs()

    def _log_routes_and_docs(self) -> None:
        """Log mapped endpoints and documentation URLs (Spring Boot style)."""
        route_metadata = getattr(self, "_route_metadata", [])
        docs_enabled = getattr(self, "_docs_enabled", False)
        host = getattr(self, "_host", None) or str(self.config.get("pyfly.web.host", "0.0.0.0"))
        port = getattr(self, "_port", None) or int(self.config.get("pyfly.web.port", 8080))

        if route_metadata:
            lines = []
            for rm in route_metadata:
                method = rm.http_method.upper()
                handler_name = rm.handler_name
                controller_name = ""
                if hasattr(rm, "handler") and hasattr(rm.handler, "__self__"):
                    controller_name = type(rm.handler.__self__).__name__ + "."
                lines.append(f"  {method:7s} {rm.path:30s} {controller_name}{handler_name}")
            self._logger.info("mapped_endpoints", count=len(route_metadata), routes="\n" + "\n".join(lines))

        if docs_enabled:
            base_url = f"http://{host}:{port}"
            self._logger.info(
                "api_documentation",
                swagger_ui=f"{base_url}/docs",
                redoc=f"{base_url}/redoc",
                openapi=f"{base_url}/openapi.json",
            )

    async def shutdown(self) -> None:
        """Shutdown the application — stop the ApplicationContext."""
        self._logger.info("shutting_down", app=self._name)
        await self._context.stop()

    def _find_config_dir(self, config_path: str | Path | None) -> Path | None:
        """Find the project directory containing config files."""
        if config_path:
            p = Path(config_path)
            return p.parent if p.is_file() else p
        for candidate in ["pyfly.yaml", "pyfly.toml", "config/pyfly.yaml", "config/pyfly.toml"]:
            if Path(candidate).exists():
                return Path(".")
        return None

    @staticmethod
    def _resolve_profiles_early(config_dir: Path | None) -> list[str]:
        """Resolve active profiles before full config load."""
        import os

        import yaml

        env_profiles = os.environ.get("PYFLY_PROFILES_ACTIVE", "")
        if env_profiles:
            return [p.strip() for p in env_profiles.split(",") if p.strip()]

        if config_dir is None:
            return []

        for candidate in [config_dir / "config" / "pyfly.yaml", config_dir / "pyfly.yaml"]:
            if candidate.exists():
                with open(candidate) as f:
                    data = yaml.safe_load(f) or {}
                profiles_value = (data.get("pyfly", {}) or {}).get("profiles", {})
                active = profiles_value.get("active", "") if isinstance(profiles_value, dict) else ""
                if active:
                    return [p.strip() for p in str(active).split(",") if p.strip()]

        return []
