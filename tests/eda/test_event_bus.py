"""Tests for event bus abstraction."""

import pytest

from pyfly.eda import InMemoryEventBus
from pyfly.eda.types import EventEnvelope


class TestInMemoryEventBus:
    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self):
        bus = InMemoryEventBus()
        received: list[EventEnvelope] = []

        async def handler(event: EventEnvelope) -> None:
            received.append(event)

        bus.subscribe("user.created", handler)
        await bus.publish("user-events", "user.created", {"id": "123", "name": "Alice"})

        assert len(received) == 1
        assert received[0].event_type == "user.created"
        assert received[0].payload["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_wildcard_subscription(self):
        bus = InMemoryEventBus()
        received: list[EventEnvelope] = []

        async def handler(event: EventEnvelope) -> None:
            received.append(event)

        bus.subscribe("user.*", handler)
        await bus.publish("events", "user.created", {"id": "1"})
        await bus.publish("events", "user.updated", {"id": "1"})
        await bus.publish("events", "order.created", {"id": "2"})

        assert len(received) == 2

    @pytest.mark.asyncio
    async def test_no_subscribers(self):
        bus = InMemoryEventBus()
        # Should not raise
        await bus.publish("topic", "event.type", {"data": "value"})

    @pytest.mark.asyncio
    async def test_envelope_has_metadata(self):
        bus = InMemoryEventBus()
        received: list[EventEnvelope] = []

        async def handler(event: EventEnvelope) -> None:
            received.append(event)

        bus.subscribe("test.event", handler)
        await bus.publish("my-topic", "test.event", {"key": "val"})

        envelope = received[0]
        assert envelope.destination == "my-topic"
        assert envelope.event_id is not None
        assert envelope.timestamp is not None
