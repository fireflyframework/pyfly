"""Tests for messaging module public exports."""
from __future__ import annotations


class TestMessagingExports:
    def test_can_import_port(self) -> None:
        from pyfly.messaging import MessageBrokerPort

        assert MessageBrokerPort is not None

    def test_can_import_message(self) -> None:
        from pyfly.messaging import Message

        assert Message is not None

    def test_can_import_memory_broker(self) -> None:
        from pyfly.messaging import InMemoryMessageBroker

        assert InMemoryMessageBroker is not None

    def test_can_import_message_listener(self) -> None:
        from pyfly.messaging import message_listener

        assert message_listener is not None
