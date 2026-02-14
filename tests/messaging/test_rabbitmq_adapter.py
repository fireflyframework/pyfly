"""Tests for RabbitMQAdapter using mock aio-pika objects."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from pyfly.messaging.adapters.rabbitmq import RabbitMQAdapter
from pyfly.messaging.ports.outbound import MessageBrokerPort


class TestRabbitMQAdapter:
    def test_protocol_compliance(self) -> None:
        adapter = RabbitMQAdapter(url="amqp://guest:guest@localhost/")
        assert isinstance(adapter, MessageBrokerPort)

    @pytest.mark.asyncio
    async def test_publish_sends_message(self) -> None:
        adapter = RabbitMQAdapter(url="amqp://localhost/")
        mock_exchange = AsyncMock()
        adapter._exchange = mock_exchange
        await adapter.publish("orders", b'{"id": 1}', key=b"order.created")
        mock_exchange.publish.assert_called_once()
        call_args = mock_exchange.publish.call_args
        assert call_args.kwargs["routing_key"] == "orders"

    @pytest.mark.asyncio
    async def test_subscribe_registers_handler(self) -> None:
        adapter = RabbitMQAdapter(url="amqp://localhost/")

        async def handler(msg):
            pass

        await adapter.subscribe("orders", handler, group="order-service")
        assert len(adapter._handlers) == 1

    @pytest.mark.asyncio
    async def test_publish_with_headers(self) -> None:
        adapter = RabbitMQAdapter(url="amqp://localhost/")
        mock_exchange = AsyncMock()
        adapter._exchange = mock_exchange
        await adapter.publish("t", b"data", headers={"type": "test"})
        mock_exchange.publish.assert_called_once()
