"""Tests for LoggingPort protocol."""

from typing import Any, runtime_checkable

from pyfly.logging.port import LoggingPort


class TestLoggingPortProtocol:
    def test_is_runtime_checkable(self):
        assert hasattr(LoggingPort, "__protocol_attrs__") or runtime_checkable

    def test_conforming_class_is_instance(self):
        class FakeLogging:
            def configure(self, config: Any) -> None:
                pass

            def get_logger(self, name: str) -> Any:
                pass

            def set_level(self, name: str, level: str) -> None:
                pass

        assert isinstance(FakeLogging(), LoggingPort)

    def test_non_conforming_class_is_not_instance(self):
        class Incomplete:
            def get_logger(self, name: str) -> Any:
                pass

        assert not isinstance(Incomplete(), LoggingPort)
