"""Tests for messaging types and port protocol."""
from __future__ import annotations

import pytest

from pyfly.messaging.ports.outbound import MessageBrokerPort
from pyfly.messaging.types import Message


class TestMessageBrokerPortProtocol:
    def test_protocol_is_runtime_checkable(self) -> None:
        """MessageBrokerPort should be usable with isinstance() checks."""

        class _FakeBroker:
            async def publish(
                self,
                topic: str,
                value: bytes,
                *,
                key: bytes | None = None,
                headers: dict[str, str] | None = None,
            ) -> None: ...

            async def subscribe(self, topic: str, handler, group: str | None = None) -> None: ...

            async def start(self) -> None: ...

            async def stop(self) -> None: ...

        assert isinstance(_FakeBroker(), MessageBrokerPort)


class TestMessage:
    def test_message_creation(self) -> None:
        """Message should be created with topic and value; key=None and headers={} by default."""
        msg = Message(topic="orders", value=b"hello")
        assert msg.topic == "orders"
        assert msg.value == b"hello"
        assert msg.key is None
        assert msg.headers == {}

    def test_message_with_key_and_headers(self) -> None:
        """Message should accept optional key and headers."""
        msg = Message(
            topic="events",
            value=b"payload",
            key=b"key-1",
            headers={"trace-id": "abc123"},
        )
        assert msg.key == b"key-1"
        assert msg.headers == {"trace-id": "abc123"}
