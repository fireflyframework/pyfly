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
"""Generic async repository built on Beanie ODM for MongoDB."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar

import pymongo

from pyfly.data.page import Page
from pyfly.data.pageable import Pageable

if TYPE_CHECKING:
    from pyfly.data.document.mongodb.specification import MongoSpecification

T = TypeVar("T")
ID = TypeVar("ID")


class MongoRepository(Generic[T, ID]):
    """Generic CRUD repository for Beanie documents.

    Mirrors ``Repository[T, ID]`` from the SQLAlchemy adapter but operates
    against MongoDB via Beanie ODM. No session injection — Beanie uses a
    globally initialised Motor client.

    Type Parameters:
        T: The document type (Beanie Document subclass).
        ID: The primary key type (typically ``PydanticObjectId`` or ``str``).

    Usage::

        repo = MongoRepository[UserDocument, str](UserDocument)
        user = await repo.save(UserDocument(name="Alice"))
        found = await repo.find_by_id(user.id)
    """

    def __init__(self, model: type[T]) -> None:
        self._model = model

    async def save(self, entity: T) -> T:
        """Persist a document (insert or update)."""
        await entity.save()  # type: ignore[union-attr]
        return entity

    async def find_by_id(self, id: ID) -> T | None:
        """Find a document by its primary key."""
        return await self._model.get(id)  # type: ignore[union-attr]

    async def find_all(self, **filters: Any) -> list[T]:
        """Find all documents, optionally filtered by field values."""
        if filters:
            return await self._model.find(filters).to_list()  # type: ignore[union-attr]
        return await self._model.find_all().to_list()  # type: ignore[union-attr]

    async def delete(self, id: ID) -> None:
        """Delete a document by its primary key."""
        entity = await self.find_by_id(id)
        if entity is not None:
            await entity.delete()  # type: ignore[union-attr]

    async def find_paginated(
        self, page: int = 1, size: int = 20, pageable: Pageable | None = None
    ) -> Page[T]:
        """Find documents with pagination.

        Args:
            page: Page number (1-based).
            size: Number of items per page.
            pageable: Optional Pageable with page, size, and sort criteria.
        """
        if pageable is not None:
            page = pageable.page
            size = pageable.size

        total = await self._model.find_all().count()  # type: ignore[union-attr]
        offset = (page - 1) * size

        query = self._model.find_all()  # type: ignore[union-attr]

        if pageable is not None:
            sort_spec = self._build_sort(pageable)
            if sort_spec:
                query = query.sort(sort_spec)

        items = await query.skip(offset).limit(size).to_list()
        return Page(items=items, total=total, page=page, size=size)

    async def count(self) -> int:
        """Return the total number of documents."""
        return await self._model.find_all().count()  # type: ignore[union-attr]

    async def exists(self, id: ID) -> bool:
        """Check if a document with the given ID exists."""
        entity = await self.find_by_id(id)
        return entity is not None

    async def find_all_by_spec(self, spec: MongoSpecification[T]) -> list[T]:
        """Find all documents matching a specification."""
        filter_doc = spec.to_predicate(self._model, {})
        if filter_doc:
            return await self._model.find(filter_doc).to_list()  # type: ignore[union-attr]
        return await self._model.find_all().to_list()  # type: ignore[union-attr]

    async def find_all_by_spec_paged(
        self, spec: MongoSpecification[T], pageable: Pageable
    ) -> Page[T]:
        """Find documents matching a specification with pagination."""
        filter_doc = spec.to_predicate(self._model, {})
        if filter_doc:
            total = await self._model.find(filter_doc).count()  # type: ignore[union-attr]
            query = self._model.find(filter_doc)  # type: ignore[union-attr]
        else:
            total = await self._model.find_all().count()  # type: ignore[union-attr]
            query = self._model.find_all()  # type: ignore[union-attr]

        sort_spec = self._build_sort(pageable)
        if sort_spec:
            query = query.sort(sort_spec)

        items = await query.skip(pageable.offset).limit(pageable.size).to_list()
        return Page(items=items, total=total, page=pageable.page, size=pageable.size)

    @staticmethod
    def _build_sort(pageable: Pageable) -> list[tuple[str, int]]:
        """Build a pymongo sort specification from a Pageable."""
        sort_spec: list[tuple[str, int]] = []
        for order in pageable.sort.orders:
            direction = pymongo.ASCENDING if order.direction == "asc" else pymongo.DESCENDING
            sort_spec.append((order.property, direction))
        return sort_spec
