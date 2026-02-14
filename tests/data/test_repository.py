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
"""Tests for Generic Repository[T] and @reactive_transactional."""

from uuid import UUID

import pytest
from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column

from pyfly.data.entity import Base, BaseEntity
from pyfly.data.page import Page
from pyfly.data.repository import Repository
from pyfly.data.transactional import reactive_transactional


class Item(BaseEntity):
    __tablename__ = "items"

    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(default=0.0)


@pytest.fixture
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
async def session(session_factory):
    async with session_factory() as session:
        yield session


@pytest.fixture
def repo(session):
    return Repository(Item, session)


class TestRepository:
    @pytest.mark.asyncio
    async def test_save_and_find_by_id(self, repo: Repository[Item], session: AsyncSession):
        item = Item(name="Widget", price=9.99)
        saved = await repo.save(item)
        assert isinstance(saved.id, UUID)

        found = await repo.find_by_id(saved.id)
        assert found is not None
        assert found.name == "Widget"
        assert found.price == 9.99

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, repo: Repository[Item]):
        from uuid import uuid4

        result = await repo.find_by_id(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_find_all(self, repo: Repository[Item]):
        await repo.save(Item(name="A", price=1.0))
        await repo.save(Item(name="B", price=2.0))
        await repo.save(Item(name="C", price=3.0))

        items = await repo.find_all()
        assert len(items) == 3

    @pytest.mark.asyncio
    async def test_delete(self, repo: Repository[Item]):
        item = await repo.save(Item(name="ToDelete", price=0.0))
        await repo.delete(item.id)

        result = await repo.find_by_id(item.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_find_paginated(self, repo: Repository[Item]):
        for i in range(15):
            await repo.save(Item(name=f"Item-{i}", price=float(i)))

        page = await repo.find_paginated(page=1, size=5)
        assert isinstance(page, Page)
        assert len(page.items) == 5
        assert page.total == 15
        assert page.total_pages == 3
        assert page.has_next is True

    @pytest.mark.asyncio
    async def test_find_paginated_last_page(self, repo: Repository[Item]):
        for i in range(12):
            await repo.save(Item(name=f"Item-{i}", price=float(i)))

        page = await repo.find_paginated(page=3, size=5)
        assert len(page.items) == 2
        assert page.total == 12
        assert page.has_next is False
        assert page.has_previous is True

    @pytest.mark.asyncio
    async def test_count(self, repo: Repository[Item]):
        await repo.save(Item(name="A"))
        await repo.save(Item(name="B"))
        assert await repo.count() == 2

    @pytest.mark.asyncio
    async def test_exists(self, repo: Repository[Item]):
        item = await repo.save(Item(name="Exists"))
        assert await repo.exists(item.id) is True

        from uuid import uuid4
        assert await repo.exists(uuid4()) is False


class TestReactiveTransactional:
    @pytest.mark.asyncio
    async def test_commits_on_success(self, session_factory):
        @reactive_transactional(session_factory)
        async def create_item(session: AsyncSession) -> Item:
            item = Item(name="Transactional", price=42.0)
            session.add(item)
            return item

        item = await create_item()
        assert item.name == "Transactional"

        # Verify it was committed
        async with session_factory() as verify_session:
            result = await verify_session.execute(select(Item).where(Item.id == item.id))
            found = result.scalar_one_or_none()
            assert found is not None
            assert found.name == "Transactional"

    @pytest.mark.asyncio
    async def test_rolls_back_on_error(self, session_factory):
        @reactive_transactional(session_factory)
        async def failing_operation(session: AsyncSession) -> None:
            session.add(Item(name="WillFail", price=0.0))
            await session.flush()
            raise ValueError("Simulated failure")

        with pytest.raises(ValueError, match="Simulated failure"):
            await failing_operation()

        # Verify nothing was committed
        async with session_factory() as verify_session:
            result = await verify_session.execute(select(Item))
            items = result.scalars().all()
            assert len(items) == 0
