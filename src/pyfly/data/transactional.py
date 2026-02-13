"""Declarative transaction management decorator."""

from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

F = TypeVar("F", bound=Callable[..., Any])


def reactive_transactional(session_factory: async_sessionmaker[AsyncSession]) -> Callable[[F], F]:
    """Decorator for declarative async transaction management.

    Wraps an async function in a database transaction. The decorated function
    receives an AsyncSession as its first argument. On success the transaction
    is committed; on exception it is rolled back and the exception re-raised.

    Usage:
        @reactive_transactional(session_factory)
        async def create_user(session: AsyncSession) -> User:
            user = User(name="Alice")
            session.add(user)
            return user
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            async with session_factory() as session:
                async with session.begin():
                    result = await func(session, *args, **kwargs)
                    return result

        return wrapper  # type: ignore[return-value]

    return decorator
