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
"""Relational data layer (SQLAlchemy) auto-configuration."""

# NOTE: No `from __future__ import annotations` — typing.get_type_hints()
# must resolve return types at runtime for @bean method registration.

import logging

try:
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
except ImportError:
    AsyncEngine = object  # type: ignore[misc,assignment]
    AsyncSession = object  # type: ignore[misc,assignment]

from pyfly.container.bean import bean
from pyfly.context.conditions import (
    auto_configuration,
    conditional_on_class,
    conditional_on_property,
)
from pyfly.core.config import Config
from pyfly.data.relational.sqlalchemy.post_processor import (
    RepositoryBeanPostProcessor,
)

_logger = logging.getLogger(__name__)


class EngineLifecycle:
    """Lifecycle wrapper that disposes the SQLAlchemy engine on shutdown.

    Implements ``start()`` / ``stop()`` so the ``ApplicationContext``
    auto-discovers it as an infrastructure adapter and calls ``stop()``
    during graceful shutdown.
    """

    def __init__(self, engine: AsyncEngine, session: AsyncSession) -> None:
        self._engine = engine
        self._session = session

    async def start(self) -> None:
        """No-op — engine is ready after creation."""

    async def stop(self) -> None:
        """Dispose engine connection pool and close the shared session."""
        try:
            await self._session.close()
        except Exception:
            _logger.debug("session_close_failed", exc_info=True)
        await self._engine.dispose()


@auto_configuration
@conditional_on_class("sqlalchemy")
@conditional_on_property("pyfly.data.relational.enabled", having_value="true")
class RelationalAutoConfiguration:
    """Auto-configures SQLAlchemy engine, session, and repository post-processor."""

    @bean
    def async_engine(self, config: Config) -> AsyncEngine:
        url = str(config.get("pyfly.data.relational.url", "sqlite+aiosqlite:///./app.db"))
        echo = bool(config.get("pyfly.data.relational.echo", False))
        return create_async_engine(url, echo=echo)

    @bean
    def async_session(self, async_engine: AsyncEngine) -> AsyncSession:
        """Create an ``AsyncSession`` from the engine.

        .. warning::
            This bean returns a **single session instance** shared across
            injections.  In production you should manage session lifecycle
            per-request (e.g. via middleware or a request-scoped provider).
            A dedicated PR should convert this to return an
            ``async_sessionmaker`` factory for proper per-operation sessions.
        """
        factory = async_sessionmaker(async_engine, expire_on_commit=False)
        return factory()

    @bean
    def engine_lifecycle(self, async_engine: AsyncEngine, async_session: AsyncSession) -> EngineLifecycle:
        """Lifecycle bean that disposes the engine on shutdown."""
        return EngineLifecycle(async_engine, async_session)

    @bean
    def repository_post_processor(self) -> RepositoryBeanPostProcessor:
        return RepositoryBeanPostProcessor()
