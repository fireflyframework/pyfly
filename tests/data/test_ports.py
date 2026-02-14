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
"""Tests for CrudRepository and PagingRepository port protocols."""

from __future__ import annotations

from pyfly.data.ports.outbound import CrudRepository, PagingRepository


class TestCrudRepository:
    def test_is_runtime_checkable(self) -> None:
        """CrudRepository should be decorated with @runtime_checkable."""
        assert hasattr(CrudRepository, "__protocol_attrs__") or isinstance(
            CrudRepository, type
        )
        # The real proof: isinstance checks don't raise TypeError
        # (they would if the protocol were not runtime_checkable).

        class _Dummy:
            async def save(self, entity): ...
            async def find_by_id(self, id): ...
            async def find_all(self): ...
            async def delete(self, entity): ...
            async def delete_by_id(self, id): ...
            async def count(self): ...
            async def exists_by_id(self, id): ...

        assert isinstance(_Dummy(), CrudRepository)

    def test_required_method_names(self) -> None:
        """CrudRepository must declare all expected CRUD methods."""
        expected = {
            "save",
            "find_by_id",
            "find_all",
            "delete",
            "delete_by_id",
            "count",
            "exists_by_id",
        }
        # Protocol methods are available via __protocol_attrs__ or callable attrs
        attrs = {
            name
            for name in dir(CrudRepository)
            if not name.startswith("_") and callable(getattr(CrudRepository, name, None))
        }
        assert expected.issubset(attrs), f"Missing methods: {expected - attrs}"


class TestPagingRepository:
    def test_defines_find_all_paged(self) -> None:
        """PagingRepository must expose find_all_paged."""
        assert hasattr(PagingRepository, "find_all_paged")
        assert callable(getattr(PagingRepository, "find_all_paged", None))

    def test_is_runtime_checkable(self) -> None:
        """PagingRepository should be runtime_checkable as well."""

        class _PagingDummy:
            async def save(self, entity): ...
            async def find_by_id(self, id): ...
            async def find_all(self): ...
            async def delete(self, entity): ...
            async def delete_by_id(self, id): ...
            async def count(self): ...
            async def exists_by_id(self, id): ...
            async def find_all_paged(self, page=1, size=20, sort=None): ...

        assert isinstance(_PagingDummy(), PagingRepository)
