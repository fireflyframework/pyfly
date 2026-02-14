"""In-memory message broker for testing and single-process applications."""
from __future__ import annotations

import itertools
from typing import Any

from pyfly.messaging.ports.outbound import MessageHandler
from pyfly.messaging.types import Message


class InMemoryMessageBroker:
    def __init__(self) -> None:
        self._subscriptions: dict[str, list[tuple[MessageHandler, str | None]]] = {}
        self._group_iterators: dict[tuple[str, str], itertools.cycle[MessageHandler]] = {}
        self._running = False

    async def publish(
        self,
        topic: str,
        value: bytes,
        *,
        key: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        msg = Message(topic=topic, value=value, key=key, headers=headers or {})
        subs = self._subscriptions.get(topic, [])
        delivered_groups: set[str] = set()
        for handler, group in subs:
            if group is None:
                await handler(msg)
            elif group not in delivered_groups:
                delivered_groups.add(group)
                rr_key = (topic, group)
                if rr_key not in self._group_iterators:
                    group_handlers = [h for h, g in subs if g == group]
                    self._group_iterators[rr_key] = itertools.cycle(group_handlers)
                selected = next(self._group_iterators[rr_key])
                await selected(msg)

    async def subscribe(
        self,
        topic: str,
        handler: MessageHandler,
        group: str | None = None,
    ) -> None:
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
        self._subscriptions[topic].append((handler, group))
        if group is not None:
            rr_key = (topic, group)
            self._group_iterators.pop(rr_key, None)

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False
