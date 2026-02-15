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
"""Auto-configuration engine with provider detection (inspired by Spring Boot auto-config)."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from pyfly.container.container import Container
    from pyfly.core.config import Config

logger = structlog.get_logger("pyfly.config.auto")


class AutoConfiguration:
    """Detect available infrastructure providers by checking importable packages."""

    @staticmethod
    def is_available(module_name: str) -> bool:
        """Check if a Python package is importable."""
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False

    @staticmethod
    def detect_cache_provider() -> str:
        """Detect the best available cache provider."""
        if AutoConfiguration.is_available("redis.asyncio"):
            return "redis"
        return "memory"

    @staticmethod
    def detect_eda_provider() -> str:
        """Detect the best available event-driven messaging provider."""
        if AutoConfiguration.is_available("aiokafka"):
            return "kafka"
        if AutoConfiguration.is_available("aio_pika"):
            return "rabbitmq"
        return "memory"

    @staticmethod
    def detect_client_provider() -> str:
        """Detect the best available HTTP client provider."""
        if AutoConfiguration.is_available("httpx"):
            return "httpx"
        return "none"

    @staticmethod
    def detect_data_provider() -> str:
        """Detect the best available data / ORM provider."""
        if AutoConfiguration.is_available("sqlalchemy"):
            return "sqlalchemy"
        return "none"


class AutoConfigurationEngine:
    """Wire adapter beans automatically based on detected providers and config.

    Reads config properties to determine which subsystems are enabled,
    detects available providers, and registers the appropriate adapter
    beans in the container. Skips any subsystem already explicitly
    registered by the user.
    """

    def __init__(self) -> None:
        self._results: dict[str, str] = {}
        self._adapters: list[Any] = []

    @property
    def results(self) -> dict[str, str]:
        """Map of subsystem -> provider that was auto-configured."""
        return dict(self._results)

    @property
    def adapters(self) -> list[Any]:
        """Adapter instances created by auto-configuration (for lifecycle management)."""
        return list(self._adapters)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def configure(self, config: Config, container: Container) -> None:
        """Run auto-configuration for all subsystems."""
        self._configure_cache(config, container)
        self._configure_messaging(config, container)
        self._configure_client(config, container)
        self._configure_data(config, container)

    def _configure_cache(self, config: Config, container: Container) -> None:
        """Auto-configure cache adapter if enabled and not already registered."""
        from pyfly.cache.ports.outbound import CacheAdapter

        if self._already_registered(container, CacheAdapter):
            return

        enabled = config.get("pyfly.cache.enabled", False)
        if not _as_bool(enabled):
            logger.info("auto_configuration", subsystem="cache", status="skipped", reason="disabled")
            return

        configured_provider = str(config.get("pyfly.cache.provider", "auto"))
        provider = (
            configured_provider
            if configured_provider != "auto"
            else AutoConfiguration.detect_cache_provider()
        )

        if provider == "redis":
            import redis.asyncio as aioredis

            from pyfly.cache.adapters.redis import RedisCacheAdapter

            url = str(config.get("pyfly.cache.redis.url", "redis://localhost:6379/0"))
            client = aioredis.from_url(url)
            adapter = RedisCacheAdapter(client=client)
            self._register(container, CacheAdapter, adapter, "cache", provider)
        else:
            from pyfly.cache.adapters.memory import InMemoryCache

            adapter = InMemoryCache()
            self._register(container, CacheAdapter, adapter, "cache", "memory")

    def _configure_messaging(self, config: Config, container: Container) -> None:
        """Auto-configure message broker if not already registered."""
        from pyfly.messaging.ports.outbound import MessageBrokerPort

        if self._already_registered(container, MessageBrokerPort):
            return

        # Skip if no messaging section exists at all (Config({}) case)
        if config.get("pyfly.messaging") is None:
            logger.info("auto_configuration", subsystem="messaging", status="skipped", reason="not configured")
            return

        configured_provider = str(config.get("pyfly.messaging.provider", "auto"))
        provider = (
            configured_provider
            if configured_provider != "auto"
            else AutoConfiguration.detect_eda_provider()
        )

        if provider == "kafka":
            from pyfly.messaging.adapters.kafka import KafkaAdapter

            servers = str(
                config.get("pyfly.messaging.kafka.bootstrap-servers", "localhost:9092")
            )
            adapter = KafkaAdapter(bootstrap_servers=servers)
            self._register(container, MessageBrokerPort, adapter, "messaging", provider)
        elif provider == "rabbitmq":
            from pyfly.messaging.adapters.rabbitmq import RabbitMQAdapter

            url = str(
                config.get(
                    "pyfly.messaging.rabbitmq.url", "amqp://guest:guest@localhost/"
                )
            )
            adapter = RabbitMQAdapter(url=url)
            self._register(container, MessageBrokerPort, adapter, "messaging", provider)
        else:
            from pyfly.messaging.adapters.memory import InMemoryMessageBroker

            adapter = InMemoryMessageBroker()
            self._register(container, MessageBrokerPort, adapter, "messaging", "memory")

    def _configure_client(self, config: Config, container: Container) -> None:
        """Auto-configure HTTP client adapter if not already registered."""
        from pyfly.client.ports.outbound import HttpClientPort

        if self._already_registered(container, HttpClientPort):
            return

        provider = AutoConfiguration.detect_client_provider()
        if provider == "httpx":
            from pyfly.client.adapters.httpx_adapter import HttpxClientAdapter

            timeout_s = int(config.get("pyfly.client.timeout", 30))
            from datetime import timedelta

            adapter = HttpxClientAdapter(timeout=timedelta(seconds=timeout_s))
            self._register(container, HttpClientPort, adapter, "client", provider)
        else:
            logger.info("auto_configuration", subsystem="client", status="skipped", reason="no provider")

    def _configure_data(self, config: Config, container: Container) -> None:
        """Auto-configure data layer if enabled and not already registered."""
        enabled = config.get("pyfly.data.enabled", False)
        if not _as_bool(enabled):
            logger.info("auto_configuration", subsystem="data", status="skipped", reason="disabled")
            return

        provider = AutoConfiguration.detect_data_provider()
        if provider == "none":
            logger.info("auto_configuration", subsystem="data", status="skipped", reason="no provider")
            return

        self._results["data"] = provider
        logger.info("auto_configuration", subsystem="data", status="configured", provider=provider)

    @staticmethod
    def _already_registered(container: Container, port_type: type) -> bool:
        """Check if a bean of the given port type is already registered."""
        return any(
            issubclass(cls, port_type)
            for cls in container._registrations
            if cls is not port_type
        )

    def _register(
        self,
        container: Container,
        port_type: type,
        instance: Any,
        subsystem: str,
        provider: str,
    ) -> None:
        """Register an adapter instance as a singleton bean."""
        from pyfly.container.types import Scope

        adapter_type = type(instance)
        container.register(adapter_type, scope=Scope.SINGLETON)
        container._registrations[adapter_type].instance = instance
        self._results[subsystem] = provider
        self._adapters.append(instance)
        logger.info("auto_configuration", subsystem=subsystem, status="configured", provider=provider)


def _as_bool(value: Any) -> bool:
    """Coerce a config value to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)
