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
"""Beanie ODM initializer — lifecycle bean that initializes Beanie on start."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorClient

    from pyfly.container.container import Container
    from pyfly.core.config import Config


class BeanieInitializer:
    """Lifecycle bean that initializes Beanie ODM during infrastructure startup.

    Scans the container for BaseDocument subclasses and calls
    ``init_beanie()`` with the Motor database and discovered models.
    """

    def __init__(
        self,
        motor_client: "AsyncIOMotorClient",
        config: "Config",
        container: "Container",
    ) -> None:
        self._motor_client = motor_client
        self._config = config
        self._container = container

    async def start(self) -> None:
        from pyfly.data.document.mongodb.document import BaseDocument

        db_name = str(self._config.get("pyfly.data.document.database", "pyfly"))

        document_models: list[type] = []
        for cls in self._container._registrations:
            if (
                isinstance(cls, type)
                and issubclass(cls, BaseDocument)
                and cls is not BaseDocument
            ):
                document_models.append(cls)

        if document_models:
            from beanie import init_beanie

            await init_beanie(
                database=self._motor_client[db_name],
                document_models=document_models,
            )

    async def stop(self) -> None:
        self._motor_client.close()
