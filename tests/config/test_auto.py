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
"""Tests for AutoConfiguration provider detection and AutoConfigurationEngine."""

from __future__ import annotations

import pytest

from pyfly.config.auto import AutoConfiguration, AutoConfigurationEngine
from pyfly.container.container import Container
from pyfly.container.exceptions import BeanCreationException
from pyfly.core.config import Config
from pyfly.kernel.exceptions import InfrastructureException


class TestAutoConfiguration:
    def test_detects_available_module(self):
        assert AutoConfiguration.is_available("json") is True

    def test_detects_unavailable_module(self):
        assert AutoConfiguration.is_available("nonexistent_xyz_module") is False

    def test_detect_cache_provider_memory(self):
        provider = AutoConfiguration.detect_cache_provider()
        assert provider in ("redis", "memory")

    def test_detect_eda_provider(self):
        provider = AutoConfiguration.detect_eda_provider()
        assert provider in ("kafka", "rabbitmq", "memory")

    def test_detect_client_provider(self):
        provider = AutoConfiguration.detect_client_provider()
        assert provider in ("httpx", "none")

    def test_detect_data_provider(self):
        provider = AutoConfiguration.detect_data_provider()
        assert provider in ("sqlalchemy", "none")


class TestAutoConfigurationEngine:
    def test_configure_skips_disabled_cache(self):
        config = Config({"pyfly": {"cache": {"enabled": False}}})
        container = Container()
        engine = AutoConfigurationEngine()
        engine.configure(config, container)
        assert "cache" not in engine.results

    def test_configure_skips_disabled_data(self):
        config = Config({"pyfly": {"data": {"enabled": False}}})
        container = Container()
        engine = AutoConfigurationEngine()
        engine.configure(config, container)
        assert "data" not in engine.results

    def test_configure_wires_memory_cache_when_enabled(self):
        config = Config({"pyfly": {"cache": {"enabled": True, "provider": "memory"}}})
        container = Container()
        engine = AutoConfigurationEngine()
        engine.configure(config, container)
        assert engine.results.get("cache") == "memory"

    def test_configure_wires_messaging(self):
        config = Config({"pyfly": {"messaging": {"provider": "memory"}}})
        container = Container()
        engine = AutoConfigurationEngine()
        engine.configure(config, container)
        assert engine.results.get("messaging") == "memory"

    def test_configure_wires_client_httpx(self):
        config = Config({"pyfly": {"client": {"timeout": 10}}})
        container = Container()
        engine = AutoConfigurationEngine()
        engine.configure(config, container)
        # httpx is available in dev env
        assert engine.results.get("client") == "httpx"

    def test_configure_data_enabled(self):
        config = Config({"pyfly": {"data": {"enabled": True}}})
        container = Container()
        engine = AutoConfigurationEngine()
        engine.configure(config, container)
        assert "data" in engine.results

    def test_configure_does_not_overwrite_existing_bean(self):
        from pyfly.cache.adapters.memory import InMemoryCache
        from pyfly.container.types import Scope

        config = Config({"pyfly": {"cache": {"enabled": True, "provider": "redis"}}})
        container = Container()
        # Pre-register a cache adapter
        container.register(InMemoryCache, scope=Scope.SINGLETON)
        container._registrations[InMemoryCache].instance = InMemoryCache()

        engine = AutoConfigurationEngine()
        engine.configure(config, container)
        # Should skip cache since it's already registered
        assert "cache" not in engine.results

    def test_results_initially_empty(self):
        engine = AutoConfigurationEngine()
        assert engine.results == {}

    def test_configure_messaging_kafka_explicit(self):
        config = Config(
            {
                "pyfly": {
                    "messaging": {
                        "provider": "kafka",
                        "kafka": {"bootstrap-servers": "localhost:9092"},
                    }
                }
            }
        )
        container = Container()
        engine = AutoConfigurationEngine()
        engine.configure(config, container)
        assert engine.results.get("messaging") == "kafka"

    def test_configure_messaging_rabbitmq_explicit(self):
        config = Config(
            {
                "pyfly": {
                    "messaging": {
                        "provider": "rabbitmq",
                        "rabbitmq": {"url": "amqp://guest:guest@localhost/"},
                    }
                }
            }
        )
        container = Container()
        engine = AutoConfigurationEngine()
        engine.configure(config, container)
        assert engine.results.get("messaging") == "rabbitmq"

    def test_adapters_tracks_auto_configured_instances(self):
        """engine.adapters should contain all auto-configured adapter instances."""
        config = Config(
            {
                "pyfly": {
                    "messaging": {"provider": "memory"},
                    "cache": {"enabled": True, "provider": "memory"},
                }
            }
        )
        container = Container()
        engine = AutoConfigurationEngine()
        engine.configure(config, container)
        # Should have at least cache + messaging adapters
        assert len(engine.adapters) >= 2
        adapter_types = {type(a).__name__ for a in engine.adapters}
        assert "InMemoryCache" in adapter_types
        assert "InMemoryMessageBroker" in adapter_types

    def test_adapters_initially_empty(self):
        engine = AutoConfigurationEngine()
        assert engine.adapters == []


class TestFailFast:
    """Fail-fast: adapter lifecycle validates connectivity during context startup."""

    def test_memory_provider_does_not_validate(self):
        """Memory providers should not trigger connectivity checks."""
        config = Config(
            {
                "pyfly": {
                    "messaging": {"provider": "memory"},
                    "cache": {"enabled": True, "provider": "memory"},
                }
            }
        )
        container = Container()
        engine = AutoConfigurationEngine()
        engine.configure(config, container)
        assert engine.results.get("messaging") == "memory"
        assert engine.results.get("cache") == "memory"

    def test_auto_detected_provider_does_not_validate(self):
        """Auto-detected providers should not fail (they fallback to memory)."""
        config = Config(
            {
                "pyfly": {
                    "messaging": {"provider": "auto"},
                }
            }
        )
        container = Container()
        engine = AutoConfigurationEngine()
        engine.configure(config, container)
        # Should succeed (auto means "detect what's available")
        assert "messaging" in engine.results

    def test_bean_creation_exception_attributes(self):
        """BeanCreationException should expose subsystem, provider, reason."""
        exc = BeanCreationException("messaging", "kafka", "Connection refused")
        assert exc.subsystem == "messaging"
        assert exc.provider == "kafka"
        assert exc.reason == "Connection refused"
        assert "messaging" in str(exc)
        assert "kafka" in str(exc)
        assert "Connection refused" in str(exc)

    def test_bean_creation_exception_inherits_infrastructure(self):
        """BeanCreationException should be an InfrastructureException."""
        exc = BeanCreationException("messaging", "kafka", "Connection refused")
        assert isinstance(exc, InfrastructureException)
        assert exc.code == "BEAN_CREATION_MESSAGING"

    def test_bean_creation_exception_has_error_code(self):
        """BeanCreationException should have a structured error code."""
        exc = BeanCreationException("cache", "redis", "timeout")
        assert exc.code == "BEAN_CREATION_CACHE"
