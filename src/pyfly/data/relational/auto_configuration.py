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


@auto_configuration
@conditional_on_class("sqlalchemy")
@conditional_on_property("pyfly.data.relational.enabled", having_value="true")
class RelationalAutoConfiguration:
    """Auto-configures SQLAlchemy engine, session, and repository post-processor."""

    @bean
    def async_engine(self, config: Config) -> AsyncEngine:
        url = str(
            config.get(
                "pyfly.data.relational.url", "sqlite+aiosqlite:///./app.db"
            )
        )
        echo = bool(config.get("pyfly.data.relational.echo", False))
        return create_async_engine(url, echo=echo)

    @bean
    def async_session(self, async_engine: AsyncEngine) -> AsyncSession:
        factory = async_sessionmaker(async_engine, expire_on_commit=False)
        return factory()

    @bean
    def repository_post_processor(self) -> RepositoryBeanPostProcessor:
        return RepositoryBeanPostProcessor()
