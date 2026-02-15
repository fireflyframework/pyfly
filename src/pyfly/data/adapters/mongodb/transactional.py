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
"""Declarative MongoDB transaction management decorator.

Requires a MongoDB replica set — standalone instances do not support
multi-document transactions.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, TypeVar

from motor.motor_asyncio import AsyncIOMotorClient

F = TypeVar("F", bound=Callable[..., Any])


def mongo_transactional(client: AsyncIOMotorClient) -> Callable[[F], F]:  # type: ignore[type-arg]
    """Decorator for declarative async MongoDB transaction management.

    Wraps an async function in a MongoDB transaction. On success the
    transaction is committed; on exception it is aborted and the exception
    re-raised.

    Requires a replica set deployment (MongoDB transactions are not
    supported on standalone instances).

    Usage::

        @mongo_transactional(motor_client)
        async def transfer_funds(from_id: str, to_id: str, amount: float) -> None:
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            async with await client.start_session() as session, session.start_transaction():
                result = await func(*args, **kwargs)
                return result

        return wrapper  # type: ignore[return-value]

    return decorator
