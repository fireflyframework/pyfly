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
"""Tests for CQRS mediator."""

from dataclasses import dataclass

import pytest

from pyfly.cqrs import Command, CommandHandler, Mediator, Query, QueryHandler, command_handler, query_handler


@dataclass(frozen=True)
class CreateUserCommand(Command):
    name: str
    email: str


@dataclass(frozen=True)
class GetUserQuery(Query):
    user_id: str


@command_handler
class CreateUserHandler(CommandHandler[CreateUserCommand]):
    async def handle(self, command: CreateUserCommand) -> dict:
        return {"id": "1", "name": command.name, "email": command.email}


@query_handler
class GetUserHandler(QueryHandler[GetUserQuery]):
    async def handle(self, query: GetUserQuery) -> dict:
        return {"id": query.user_id, "name": "Alice"}


class TestMediator:
    @pytest.mark.asyncio
    async def test_dispatch_command(self):
        mediator = Mediator()
        mediator.register_handler(CreateUserCommand, CreateUserHandler())

        result = await mediator.send(CreateUserCommand(name="Alice", email="alice@test.com"))
        assert result["name"] == "Alice"
        assert result["id"] == "1"

    @pytest.mark.asyncio
    async def test_dispatch_query(self):
        mediator = Mediator()
        mediator.register_handler(GetUserQuery, GetUserHandler())

        result = await mediator.send(GetUserQuery(user_id="42"))
        assert result["id"] == "42"
        assert result["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_unregistered_command_raises(self):
        mediator = Mediator()
        with pytest.raises(KeyError, match="No handler registered"):
            await mediator.send(CreateUserCommand(name="Bob", email="bob@test.com"))

    def test_command_handler_decorator_marks_class(self):
        assert getattr(CreateUserHandler, "__pyfly_handler_type__", None) == "command"

    def test_query_handler_decorator_marks_class(self):
        assert getattr(GetUserHandler, "__pyfly_handler_type__", None) == "query"
