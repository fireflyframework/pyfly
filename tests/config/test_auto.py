"""Tests for AutoConfiguration provider detection."""

from pyfly.config.auto import AutoConfiguration


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
