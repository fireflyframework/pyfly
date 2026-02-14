"""Kafka message broker adapter — wraps aiokafka."""
from __future__ import annotations

import asyncio
from typing import Any

from pyfly.messaging.ports.outbound import MessageHandler
from pyfly.messaging.types import Message


class KafkaAdapter:
    """MessageBrokerPort implementation backed by Apache Kafka via aiokafka.

    Requires aiokafka to be installed (pip install pyfly[kafka]).
    """

    def __init__(self, bootstrap_servers: str = "localhost:9092") -> None:
        self._bootstrap_servers = bootstrap_servers
        self._producer: Any = None
        self._consumers: list[Any] = []
        self._handlers: list[tuple[str, MessageHandler, str | None]] = []
        self._consumer_tasks: list[asyncio.Task[None]] = []

    async def publish(
        self,
        topic: str,
        value: bytes,
        *,
        key: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        kafka_headers = (
            [(k, v.encode()) for k, v in headers.items()] if headers else None
        )
        await self._producer.send_and_wait(
            topic, value=value, key=key, headers=kafka_headers
        )

    async def subscribe(
        self,
        topic: str,
        handler: MessageHandler,
        group: str | None = None,
    ) -> None:
        self._handlers.append((topic, handler, group))

    async def start(self) -> None:
        from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers
        )
        await self._producer.start()

        grouped: dict[tuple[str, str | None], list[tuple[str, MessageHandler]]] = {}
        for topic, handler, group in self._handlers:
            key = (topic, group)
            grouped.setdefault(key, []).append((topic, handler))

        for (topic, group), entries in grouped.items():
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self._bootstrap_servers,
                group_id=group,
            )
            await consumer.start()
            self._consumers.append(consumer)
            handlers_for_consumer = [h for _, h in entries]
            task = asyncio.create_task(
                self._consume_loop(consumer, handlers_for_consumer)
            )
            self._consumer_tasks.append(task)

    async def stop(self) -> None:
        for task in self._consumer_tasks:
            task.cancel()
        for consumer in self._consumers:
            await consumer.stop()
        if self._producer is not None:
            await self._producer.stop()

    async def _consume_loop(
        self, consumer: Any, handlers: list[MessageHandler]
    ) -> None:
        try:
            async for record in consumer:
                headers = (
                    {k: v.decode() for k, v in record.headers}
                    if record.headers
                    else {}
                )
                msg = Message(
                    topic=record.topic,
                    value=record.value,
                    key=record.key,
                    headers=headers,
                )
                for handler in handlers:
                    await handler(msg)
        except asyncio.CancelledError:
            pass
