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
"""Tests for declarative @http_client and HTTP method decorators."""
from __future__ import annotations

import pytest

from pyfly.client.declarative import delete, get, http_client, patch, post, put
from pyfly.container.types import Scope


class TestHttpClientDecorator:
    def test_marks_class_with_metadata(self) -> None:
        @http_client(base_url="http://example.com")
        class MyClient:
            pass

        assert getattr(MyClient, "__pyfly_http_client__") is True
        assert getattr(MyClient, "__pyfly_http_base_url__") == "http://example.com"

    def test_marks_class_as_injectable(self) -> None:
        @http_client(base_url="http://example.com")
        class MyClient:
            pass

        assert getattr(MyClient, "__pyfly_injectable__") is True
        assert getattr(MyClient, "__pyfly_stereotype__") == "component"
        assert getattr(MyClient, "__pyfly_scope__") is Scope.SINGLETON


class TestHttpMethodDecorators:
    def test_get_decorator(self) -> None:
        @get("/items/{item_id}")
        async def get_item(self, item_id: str) -> dict: ...

        assert getattr(get_item, "__pyfly_http_method__") == "GET"
        assert getattr(get_item, "__pyfly_http_path__") == "/items/{item_id}"

    def test_post_decorator(self) -> None:
        @post("/items")
        async def create_item(self, body: dict) -> dict: ...

        assert getattr(create_item, "__pyfly_http_method__") == "POST"
        assert getattr(create_item, "__pyfly_http_path__") == "/items"

    def test_put_decorator(self) -> None:
        @put("/items/{item_id}")
        async def update_item(self, item_id: str, body: dict) -> dict: ...

        assert getattr(update_item, "__pyfly_http_method__") == "PUT"
        assert getattr(update_item, "__pyfly_http_path__") == "/items/{item_id}"

    def test_delete_decorator(self) -> None:
        @delete("/items/{item_id}")
        async def delete_item(self, item_id: str) -> None: ...

        assert getattr(delete_item, "__pyfly_http_method__") == "DELETE"
        assert getattr(delete_item, "__pyfly_http_path__") == "/items/{item_id}"

    def test_patch_decorator(self) -> None:
        @patch("/items/{item_id}")
        async def patch_item(self, item_id: str, body: dict) -> dict: ...

        assert getattr(patch_item, "__pyfly_http_method__") == "PATCH"
        assert getattr(patch_item, "__pyfly_http_path__") == "/items/{item_id}"

    def test_multiple_methods_on_one_client(self) -> None:
        @http_client(base_url="http://api.example.com")
        class ItemClient:
            @get("/items/{item_id}")
            async def get_item(self, item_id: str) -> dict: ...

            @post("/items")
            async def create_item(self, body: dict) -> dict: ...

            @delete("/items/{item_id}")
            async def delete_item(self, item_id: str) -> None: ...

        get_method = ItemClient.get_item
        post_method = ItemClient.create_item
        delete_method = ItemClient.delete_item

        assert getattr(get_method, "__pyfly_http_method__") == "GET"
        assert getattr(get_method, "__pyfly_http_path__") == "/items/{item_id}"
        assert getattr(post_method, "__pyfly_http_method__") == "POST"
        assert getattr(post_method, "__pyfly_http_path__") == "/items"
        assert getattr(delete_method, "__pyfly_http_method__") == "DELETE"
        assert getattr(delete_method, "__pyfly_http_path__") == "/items/{item_id}"

    @pytest.mark.asyncio
    async def test_placeholder_raises_not_implemented(self) -> None:
        @http_client(base_url="http://example.com")
        class MyClient:
            @get("/items")
            async def list_items(self) -> list: ...

        client = MyClient()
        with pytest.raises(NotImplementedError, match="has not been wired"):
            await client.list_items()
