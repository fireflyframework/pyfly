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
"""Beanie ODM initializer helper."""

from __future__ import annotations

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient


async def initialize_beanie(
    uri: str,
    database: str,
    document_models: list[type],
) -> AsyncIOMotorClient:  # type: ignore[type-arg]
    """Initialize Beanie with a Motor client and document models.

    Creates a Motor client, connects to the specified database, and
    initialises Beanie with the provided document models.

    Args:
        uri: MongoDB connection URI (e.g. ``mongodb://localhost:27017``).
        database: Database name.
        document_models: List of Beanie Document subclasses to register.

    Returns:
        The Motor client instance for lifecycle management.
    """
    client: AsyncIOMotorClient = AsyncIOMotorClient(uri)  # type: ignore[type-arg]
    await init_beanie(database=client[database], document_models=document_models)
    return client
