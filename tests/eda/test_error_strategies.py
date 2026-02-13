"""Tests for EDA hexagonal ports and error strategies."""

from pyfly.eda.ports.outbound import EventPublisher
from pyfly.eda.types import ErrorStrategy


class TestErrorStrategy:
    def test_enum_values(self):
        assert ErrorStrategy.IGNORE.value == "IGNORE"
        assert ErrorStrategy.LOG_AND_CONTINUE.value == "LOG_AND_CONTINUE"
        assert ErrorStrategy.RETRY.value == "RETRY"
        assert ErrorStrategy.DEAD_LETTER.value == "DEAD_LETTER"
        assert ErrorStrategy.FAIL_FAST.value == "FAIL_FAST"


class TestEventPublisherProtocol:
    def test_in_memory_implements_publisher(self):
        from pyfly.eda.adapters.memory import InMemoryEventBus
        bus = InMemoryEventBus()
        assert isinstance(bus, EventPublisher)
