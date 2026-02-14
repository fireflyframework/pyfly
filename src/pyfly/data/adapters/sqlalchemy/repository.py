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
"""Generic async repository built on SQLAlchemy 2.0."""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from pyfly.data.adapters.sqlalchemy.entity import BaseEntity
from pyfly.data.page import Page
from pyfly.data.pageable import Pageable
from pyfly.data.specification import Specification

T = TypeVar("T", bound=BaseEntity)


class Repository(Generic[T]):
    """Generic CRUD repository for SQLAlchemy entities.

    Provides standard data access operations with async support.
    Subclass to add custom queries for specific entities.

    Usage:
        repo = Repository(User, session)
        user = await repo.save(User(name="Alice"))
        found = await repo.find_by_id(user.id)
    """

    def __init__(self, model: type[T], session: AsyncSession) -> None:
        self._model = model
        self._session = session

    async def save(self, entity: T) -> T:
        """Persist an entity (insert or update)."""
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def find_by_id(self, id: UUID) -> T | None:
        """Find an entity by its primary key."""
        return await self._session.get(self._model, id)

    async def find_all(self, **filters: Any) -> list[T]:
        """Find all entities, optionally filtered by column values."""
        stmt = select(self._model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self._model, key) == value)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, id: UUID) -> None:
        """Delete an entity by its primary key."""
        entity = await self.find_by_id(id)
        if entity is not None:
            await self._session.delete(entity)
            await self._session.flush()

    async def find_paginated(
        self, page: int = 1, size: int = 20, pageable: Pageable | None = None
    ) -> Page[T]:
        """Find entities with pagination.

        Args:
            page: Page number (1-based).
            size: Number of items per page.
            pageable: Optional Pageable with page, size, and sort criteria.
                      When provided, its page/size/sort override the primitives.

        Returns:
            A Page[T] containing the results and pagination metadata.
        """
        if pageable is not None:
            page = pageable.page
            size = pageable.size

        # Count total
        count_stmt = select(func.count()).select_from(self._model)
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        # Fetch page
        offset = (page - 1) * size
        stmt = select(self._model)

        # Apply sorting from pageable
        if pageable is not None:
            for order in pageable.sort.orders:
                col = getattr(self._model, order.property)
                stmt = stmt.order_by(
                    col.asc() if order.direction == "asc" else col.desc()
                )

        stmt = stmt.offset(offset).limit(size)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return Page(items=items, total=total, page=page, size=size)

    async def find_all_by_spec(self, spec: Specification[T]) -> list[T]:
        """Find all entities matching the specification."""
        stmt = select(self._model)
        stmt = spec.to_predicate(self._model, stmt)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_all_by_spec_paged(
        self, spec: Specification[T], pageable: Pageable
    ) -> Page[T]:
        """Find entities matching the specification with pagination and sorting."""
        # Count with spec
        base = select(self._model)
        filtered = spec.to_predicate(self._model, base)
        count_stmt = select(func.count()).select_from(filtered.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply sorting from Pageable.sort
        stmt = filtered
        for order in pageable.sort.orders:
            col = getattr(self._model, order.property)
            stmt = stmt.order_by(
                col.asc() if order.direction == "asc" else col.desc()
            )

        # Apply pagination
        stmt = stmt.offset(pageable.offset).limit(pageable.size)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return Page(items=items, total=total, page=pageable.page, size=pageable.size)

    async def count(self) -> int:
        """Return the total number of entities."""
        stmt = select(func.count()).select_from(self._model)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def exists(self, id: UUID) -> bool:
        """Check if an entity with the given ID exists."""
        entity = await self.find_by_id(id)
        return entity is not None
