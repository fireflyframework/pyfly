"""Tests for @Value descriptor — injects config values into bean fields."""

import pytest

from pyfly.core.config import Config
from pyfly.core.value import Value


class TestValue:
    """Unit tests for the Value descriptor."""

    def test_resolve_simple_key(self):
        config = Config({"pyfly": {"app": {"name": "MyApp"}}})
        val = Value("${pyfly.app.name}")
        result = val.resolve(config)
        assert result == "MyApp"

    def test_resolve_with_default(self):
        config = Config({})
        val = Value("${pyfly.missing.key:fallback}")
        result = val.resolve(config)
        assert result == "fallback"

    def test_resolve_missing_no_default_raises(self):
        config = Config({})
        val = Value("${pyfly.missing.key}")
        with pytest.raises(KeyError, match="pyfly.missing.key"):
            val.resolve(config)

    def test_resolve_literal_string(self):
        """Non-placeholder strings are returned as-is."""
        config = Config({})
        val = Value("literal-value")
        result = val.resolve(config)
        assert result == "literal-value"

    def test_resolve_empty_default(self):
        config = Config({})
        val = Value("${pyfly.key:}")
        result = val.resolve(config)
        assert result == ""

    def test_resolve_int_value(self):
        config = Config({"pyfly": {"server": {"port": 8080}}})
        val = Value("${pyfly.server.port}")
        result = val.resolve(config)
        assert result == 8080

    def test_descriptor_protocol(self):
        """Value works as a class-level descriptor placeholder."""
        val = Value("${pyfly.app.name}")
        assert val.expression == "${pyfly.app.name}"
