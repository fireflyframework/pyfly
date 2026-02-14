"""Tests for StructlogAdapter — default LoggingPort implementation."""

from pyfly.core.config import Config
from pyfly.logging.port import LoggingPort
from pyfly.logging.structlog_adapter import StructlogAdapter


class TestStructlogAdapterConformance:
    def test_implements_logging_port(self):
        adapter = StructlogAdapter()
        assert isinstance(adapter, LoggingPort)


class TestStructlogAdapterConfigure:
    def test_configure_with_defaults(self):
        adapter = StructlogAdapter()
        config = Config({})
        adapter.configure(config)

    def test_configure_reads_root_level(self):
        adapter = StructlogAdapter()
        config = Config({"logging": {"level": {"root": "DEBUG"}}})
        adapter.configure(config)
        assert adapter._root_level == "DEBUG"

    def test_configure_reads_format(self):
        adapter = StructlogAdapter()
        config = Config({"logging": {"format": "json"}})
        adapter.configure(config)
        assert adapter._format == "json"

    def test_configure_defaults_console_format(self):
        adapter = StructlogAdapter()
        config = Config({})
        adapter.configure(config)
        assert adapter._format == "console"

    def test_configure_reads_per_module_levels(self):
        adapter = StructlogAdapter()
        config = Config({"logging": {"level": {"root": "INFO", "myapp.services": "DEBUG"}}})
        adapter.configure(config)
        assert adapter._module_levels == {"myapp.services": "DEBUG"}


class TestStructlogAdapterGetLogger:
    def test_get_logger_returns_bound_logger(self):
        adapter = StructlogAdapter()
        adapter.configure(Config({}))
        logger = adapter.get_logger("myapp.test")
        assert logger is not None
        assert callable(getattr(logger, "info", None))
        assert callable(getattr(logger, "debug", None))

    def test_get_logger_different_names(self):
        adapter = StructlogAdapter()
        adapter.configure(Config({}))
        a = adapter.get_logger("a")
        b = adapter.get_logger("b")
        assert a is not None
        assert b is not None


class TestStructlogAdapterSetLevel:
    def test_set_level_updates_module_level(self):
        adapter = StructlogAdapter()
        adapter.configure(Config({}))
        adapter.set_level("myapp.services", "DEBUG")
        import logging

        assert logging.getLogger("myapp.services").level == logging.DEBUG
