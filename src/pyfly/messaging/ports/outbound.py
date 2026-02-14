"""Outbound port for message broker operations."""
from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any, Protocol, runtime_checkable

from pyfly.messaging.types import Message

MessageHandler = Callable[[Message], Coroutine[Any, Any, None]]


@runtime_checkable
class MessageBrokerPort(Protocol):
    async def publish(
        self,
        topic: str,
        value: bytes,
        *,
        key: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> None: ...

    async def subscribe(
        self,
        topic: str,
        handler: MessageHandler,
        group: str | None = None,
    ) -> None: ...

    async def start(self) -> None: ...

    async def stop(self) -> None: ...
