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
"""CQRS base types."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Command:
    """Base class for commands (write operations)."""


class Query:
    """Base class for queries (read operations)."""


class CommandHandler(Generic[T]):
    """Base class for command handlers."""

    async def handle(self, command: T) -> Any:
        raise NotImplementedError


class QueryHandler(Generic[T]):
    """Base class for query handlers."""

    async def handle(self, query: T) -> Any:
        raise NotImplementedError
