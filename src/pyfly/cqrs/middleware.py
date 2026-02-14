# Copyright 2026 Firefly Software Solutions Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""CQRS middleware pipeline — cross-cutting concerns for command/query handling."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol


class CqrsMiddleware(Protocol):
    """Middleware that wraps command/query execution."""

    async def handle(self, message: Any, next_handler: Callable[..., Awaitable[Any]]) -> Any: ...


class LoggingMiddleware:
    """Logs command/query execution."""

    def __init__(self, logger: Any = None) -> None:
        self._logger = logger

    async def handle(self, message: Any, next_handler: Callable[..., Awaitable[Any]]) -> Any:
        msg_type = type(message).__name__
        if self._logger:
            self._logger.info(f"Handling {msg_type}", message_type=msg_type)
        result = await next_handler(message)
        if self._logger:
            self._logger.info(f"Completed {msg_type}", message_type=msg_type)
        return result


class MetricsMiddleware:
    """Records execution metrics for commands/queries."""

    def __init__(self, registry: Any = None) -> None:
        self._counter = registry.counter("cqrs_messages_total", "Total CQRS messages handled") if registry else None

    async def handle(self, message: Any, next_handler: Callable[..., Awaitable[Any]]) -> Any:
        if self._counter:
            self._counter.inc()
        return await next_handler(message)
