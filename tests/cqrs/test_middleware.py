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
"""Tests for CQRS middleware pipeline."""

from dataclasses import dataclass

import pytest

from pyfly.cqrs import Command, CommandHandler, Mediator
from pyfly.cqrs.middleware import CqrsMiddleware, LoggingMiddleware, MetricsMiddleware


@dataclass(frozen=True)
class EchoCommand(Command):
    message: str


class EchoHandler(CommandHandler[EchoCommand]):
    async def handle(self, command: EchoCommand) -> str:
        return command.message


class TestMiddlewarePipeline:
    @pytest.mark.asyncio
    async def test_mediator_with_no_middleware(self):
        mediator = Mediator()
        mediator.register_handler(EchoCommand, EchoHandler())
        result = await mediator.send(EchoCommand(message="hello"))
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_middleware_executes_in_order(self):
        execution_log: list[str] = []

        class TrackingMiddleware(CqrsMiddleware):
            def __init__(self, name: str):
                self._name = name

            async def handle(self, message, next_handler):
                execution_log.append(f"{self._name}:before")
                result = await next_handler(message)
                execution_log.append(f"{self._name}:after")
                return result

        mediator = Mediator(middleware=[
            TrackingMiddleware("first"),
            TrackingMiddleware("second"),
        ])
        mediator.register_handler(EchoCommand, EchoHandler())

        result = await mediator.send(EchoCommand(message="test"))
        assert result == "test"
        assert execution_log == ["first:before", "second:before", "second:after", "first:after"]

    @pytest.mark.asyncio
    async def test_logging_middleware(self):
        logged: list[str] = []

        class CapturingLogger:
            def info(self, msg, **kwargs):
                logged.append(msg)

        middleware = LoggingMiddleware(logger=CapturingLogger())
        mediator = Mediator(middleware=[middleware])
        mediator.register_handler(EchoCommand, EchoHandler())

        await mediator.send(EchoCommand(message="test"))
        assert any("EchoCommand" in msg for msg in logged)

    @pytest.mark.asyncio
    async def test_metrics_middleware_counts(self):
        counts: dict[str, int] = {}

        class FakeCounter:
            def __init__(self, name):
                self._name = name
            def inc(self):
                counts[self._name] = counts.get(self._name, 0) + 1

        class FakeRegistry:
            def counter(self, name, description):
                return FakeCounter(name)

        middleware = MetricsMiddleware(registry=FakeRegistry())
        mediator = Mediator(middleware=[middleware])
        mediator.register_handler(EchoCommand, EchoHandler())

        await mediator.send(EchoCommand(message="test"))
        assert counts.get("cqrs_messages_total", 0) == 1

    @pytest.mark.asyncio
    async def test_middleware_can_short_circuit(self):
        class RejectMiddleware(CqrsMiddleware):
            async def handle(self, message, next_handler):
                return "rejected"

        mediator = Mediator(middleware=[RejectMiddleware()])
        mediator.register_handler(EchoCommand, EchoHandler())

        result = await mediator.send(EchoCommand(message="test"))
        assert result == "rejected"
