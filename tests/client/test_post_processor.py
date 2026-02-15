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
"""Tests for HttpClientBeanPostProcessor."""
from __future__ import annotations

import json

import pytest

from pyfly.client.declarative import get, http_client, post
from pyfly.client.post_processor import HttpClientBeanPostProcessor


class FakeHttpClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.response_body: bytes = b"{}"
        self.response_status: int = 200

    async def request(self, method: str, url: str, **kwargs) -> "FakeResponse":
        self.calls.append({"method": method, "url": url, **kwargs})
        return FakeResponse(self.response_body, self.response_status)

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass


class FakeResponse:
    def __init__(self, body: bytes, status_code: int = 200) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> dict:
        return json.loads(self._body)

    @property
    def text(self) -> str:
        return self._body.decode()


class TestHttpClientBeanPostProcessor:
    @pytest.mark.asyncio
    async def test_wires_get_method(self) -> None:
        @http_client(base_url="http://api.example.com")
        class ItemClient:
            @get("/items/{item_id}")
            async def get_item(self, item_id: str) -> dict: ...

        fake = FakeHttpClient()
        fake.response_body = json.dumps({"id": "abc", "name": "Widget"}).encode()
        processor = HttpClientBeanPostProcessor(
            http_client_factory=lambda base_url: fake,
        )
        bean = ItemClient()
        processor.before_init(bean, "itemClient")
        processor.after_init(bean, "itemClient")
        result = await bean.get_item("abc")
        assert result == {"id": "abc", "name": "Widget"}
        assert fake.calls[0]["method"] == "GET"
        assert fake.calls[0]["url"] == "/items/abc"

    @pytest.mark.asyncio
    async def test_wires_post_method_with_body(self) -> None:
        @http_client(base_url="http://api.example.com")
        class ItemClient:
            @post("/items")
            async def create_item(self, body: dict) -> dict: ...

        fake = FakeHttpClient()
        fake.response_body = json.dumps({"id": "new"}).encode()
        processor = HttpClientBeanPostProcessor(
            http_client_factory=lambda base_url: fake,
        )
        bean = ItemClient()
        processor.before_init(bean, "itemClient")
        processor.after_init(bean, "itemClient")
        result = await bean.create_item(body={"name": "Widget"})
        assert result == {"id": "new"}
        assert fake.calls[0]["method"] == "POST"

    def test_skips_non_http_client_beans(self) -> None:
        class RegularBean:
            pass

        processor = HttpClientBeanPostProcessor()
        bean = RegularBean()
        result = processor.after_init(bean, "regularBean")
        assert result is bean

    @pytest.mark.asyncio
    async def test_path_variable_substitution(self) -> None:
        @http_client(base_url="http://example.com")
        class UserClient:
            @get("/users/{user_id}/posts/{post_id}")
            async def get_post(self, user_id: int, post_id: int) -> dict: ...

        fake = FakeHttpClient()
        fake.response_body = b'{"title": "Hello"}'
        processor = HttpClientBeanPostProcessor(
            http_client_factory=lambda base_url: fake,
        )
        bean = UserClient()
        processor.before_init(bean, "userClient")
        processor.after_init(bean, "userClient")
        await bean.get_post(42, 7)
        assert fake.calls[0]["url"] == "/users/42/posts/7"
