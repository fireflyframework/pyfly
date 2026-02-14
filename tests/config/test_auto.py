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

from unittest.mock import patch

import pytest

from pyfly.config.auto import AutoConfiguration, AutoConfigurationEngine
from pyfly.container.container import Container
from pyfly.container.exceptions import BeanCreationException
from pyfly.core.config import Config


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

    @patch.object(AutoConfigurationEngine, "_check_connectivity", return_value=True)
    def test_configure_messaging_kafka_explicit(self, _mock_conn):
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

    @patch.object(AutoConfigurationEngine, "_check_connectivity", return_value=True)
    def test_configure_messaging_rabbitmq_explicit(self, _mock_conn):
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


class TestFailFast:
    """Fail-fast: explicitly-configured infrastructure must be reachable."""

    def test_kafka_unreachable_raises(self):
        """When provider=kafka and Kafka is unreachable, should raise BeanCreationException."""
        config = Config(
            {
                "pyfly": {
                    "messaging": {
                        "provider": "kafka",
                        "kafka": {"bootstrap-servers": "localhost:19999"},
                    }
                }
            }
        )
        container = Container()
        engine = AutoConfigurationEngine()
        with pytest.raises(BeanCreationException, match="messaging.*kafka"):
            engine.configure(config, container)

    def test_rabbitmq_unreachable_raises(self):
        """When provider=rabbitmq and RabbitMQ is unreachable, should raise BeanCreationException."""
        config = Config(
            {
                "pyfly": {
                    "messaging": {
                        "provider": "rabbitmq",
                        "rabbitmq": {"url": "amqp://guest:guest@localhost:19998/"},
                    }
                }
            }
        )
        container = Container()
        engine = AutoConfigurationEngine()
        with pytest.raises(BeanCreationException, match="messaging.*rabbitmq"):
            engine.configure(config, container)

    def test_redis_unreachable_raises(self):
        """When provider=redis and Redis is unreachable, should raise BeanCreationException."""
        config = Config(
            {
                "pyfly": {
                    "cache": {
                        "enabled": True,
                        "provider": "redis",
                        "redis": {"url": "redis://localhost:19997/0"},
                    }
                }
            }
        )
        container = Container()
        engine = AutoConfigurationEngine()
        with pytest.raises(BeanCreationException, match="cache.*redis"):
            engine.configure(config, container)

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

    @patch.object(AutoConfigurationEngine, "_check_connectivity", return_value=True)
    def test_kafka_reachable_does_not_raise(self, _mock_conn):
        """When Kafka IS reachable, explicit config should succeed."""
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

    @patch.object(AutoConfigurationEngine, "_check_connectivity", return_value=True)
    def test_redis_reachable_does_not_raise(self, _mock_conn):
        """When Redis IS reachable, explicit config should succeed."""
        config = Config(
            {
                "pyfly": {
                    "cache": {
                        "enabled": True,
                        "provider": "redis",
                        "redis": {"url": "redis://localhost:6379/0"},
                    }
                }
            }
        )
        container = Container()
        engine = AutoConfigurationEngine()
        engine.configure(config, container)
        assert engine.results.get("cache") == "redis"

    def test_check_connectivity_helper(self):
        """The _check_connectivity helper should return False for unreachable port."""
        assert AutoConfigurationEngine._check_connectivity("localhost", 19999, timeout=0.5) is False
