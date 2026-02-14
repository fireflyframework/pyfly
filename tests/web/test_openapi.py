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
"""Tests for OpenAPI 3.1 schema generator."""

import pytest
from pydantic import BaseModel
from starlette.testclient import TestClient

from pyfly.container.stereotypes import rest_controller, service
from pyfly.context.application_context import ApplicationContext
from pyfly.core.config import Config
from pyfly.web.app import create_app
from pyfly.web.controller import ControllerRegistrar, RouteMetadata, _py_type_to_openapi
from pyfly.web.mappings import (
    delete_mapping,
    get_mapping,
    post_mapping,
    put_mapping,
    request_mapping,
)
from pyfly.web.openapi import OpenAPIGenerator
from pyfly.web.params import Body, Cookie, Header, PathVar, QueryParam


# ---- Test models and controllers -------------------------------------------


class CreateItemRequest(BaseModel):
    name: str
    description: str = ""


class UpdateItemRequest(BaseModel):
    name: str


@service
class CatalogService:
    def get_item(self, item_id: str) -> dict:
        return {"id": item_id, "name": "Widget"}

    def list_items(self, page: int) -> list[dict]:
        return [{"id": "1", "name": "Widget"}]

    def create_item(self, name: str) -> dict:
        return {"id": "new-1", "name": name}

    def update_item(self, item_id: str, name: str) -> dict:
        return {"id": item_id, "name": name}


@rest_controller
@request_mapping("/api/items")
class CatalogController:
    def __init__(self, catalog_service: CatalogService):
        self._svc = catalog_service

    @get_mapping("/{item_id}")
    async def get_item(self, item_id: PathVar[str]) -> dict:
        return self._svc.get_item(item_id)

    @get_mapping("/")
    async def list_items(self, page: QueryParam[int] = 1) -> list:
        return self._svc.list_items(page)

    @post_mapping("/", status_code=201)
    async def create_item(self, body: Body[CreateItemRequest]) -> dict:
        return self._svc.create_item(body.name)

    @put_mapping("/{item_id}")
    async def update_item(
        self, item_id: PathVar[str], body: Body[UpdateItemRequest]
    ) -> dict:
        return self._svc.update_item(item_id, body.name)

    @delete_mapping("/{item_id}", status_code=204)
    async def delete_item(self, item_id: PathVar[str]) -> None:
        pass


@rest_controller
@request_mapping("/api/advanced")
class AdvancedController:
    @get_mapping("/")
    async def with_header_and_cookie(
        self,
        x_api_key: Header[str] = "",
        session_id: Cookie[str] = "",
    ) -> dict:
        return {"key": x_api_key, "session": session_id}


# ---- Tests -----------------------------------------------------------------


class TestOpenAPIGenerator:
    """Basic spec generation (no route metadata)."""

    def test_basic_spec(self):
        gen = OpenAPIGenerator(title="Test API", version="1.0.0")
        spec = gen.generate()
        assert spec["openapi"] == "3.1.0"
        assert spec["info"]["title"] == "Test API"
        assert spec["info"]["version"] == "1.0.0"

    def test_description(self):
        gen = OpenAPIGenerator(title="Test", version="1.0", description="My API")
        spec = gen.generate()
        assert spec["info"]["description"] == "My API"

    def test_empty_paths(self):
        gen = OpenAPIGenerator(title="Test", version="1.0")
        spec = gen.generate()
        assert spec["paths"] == {}

    def test_no_components_when_no_models(self):
        gen = OpenAPIGenerator(title="Test", version="1.0")
        spec = gen.generate()
        assert "components" not in spec


class TestPyTypeToOpenapi:
    """Unit tests for the type mapping helper."""

    def test_int(self):
        assert _py_type_to_openapi(int) == "integer"

    def test_float(self):
        assert _py_type_to_openapi(float) == "number"

    def test_bool(self):
        assert _py_type_to_openapi(bool) == "boolean"

    def test_str(self):
        assert _py_type_to_openapi(str) == "string"

    def test_default_fallback(self):
        assert _py_type_to_openapi(bytes) == "string"


class TestCollectRouteMetadata:
    """Tests for ControllerRegistrar.collect_route_metadata()."""

    @pytest.mark.asyncio
    async def test_metadata_collected(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(CatalogService)
        ctx.register_bean(CatalogController)
        await ctx.start()

        registrar = ControllerRegistrar()
        metadata = registrar.collect_route_metadata(ctx)
        assert len(metadata) >= 5  # get, list, create, update, delete

    @pytest.mark.asyncio
    async def test_metadata_is_route_metadata_instances(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(CatalogService)
        ctx.register_bean(CatalogController)
        await ctx.start()

        registrar = ControllerRegistrar()
        metadata = registrar.collect_route_metadata(ctx)
        for m in metadata:
            assert isinstance(m, RouteMetadata)

    @pytest.mark.asyncio
    async def test_path_params_extracted(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(CatalogService)
        ctx.register_bean(CatalogController)
        await ctx.start()

        registrar = ControllerRegistrar()
        metadata = registrar.collect_route_metadata(ctx)
        get_item = next(m for m in metadata if m.handler_name == "get_item")
        path_params = [p for p in get_item.parameters if p["in"] == "path"]
        assert len(path_params) == 1
        assert path_params[0]["name"] == "item_id"
        assert path_params[0]["required"] is True

    @pytest.mark.asyncio
    async def test_query_params_extracted(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(CatalogService)
        ctx.register_bean(CatalogController)
        await ctx.start()

        registrar = ControllerRegistrar()
        metadata = registrar.collect_route_metadata(ctx)
        list_items = next(m for m in metadata if m.handler_name == "list_items")
        query_params = [p for p in list_items.parameters if p["in"] == "query"]
        assert len(query_params) == 1
        assert query_params[0]["name"] == "page"
        assert query_params[0]["schema"]["type"] == "integer"

    @pytest.mark.asyncio
    async def test_body_model_extracted(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(CatalogService)
        ctx.register_bean(CatalogController)
        await ctx.start()

        registrar = ControllerRegistrar()
        metadata = registrar.collect_route_metadata(ctx)
        create_item = next(m for m in metadata if m.handler_name == "create_item")
        assert create_item.request_body_model is CreateItemRequest

    @pytest.mark.asyncio
    async def test_header_and_cookie_extracted(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(AdvancedController)
        await ctx.start()

        registrar = ControllerRegistrar()
        metadata = registrar.collect_route_metadata(ctx)
        handler = next(m for m in metadata if m.handler_name == "with_header_and_cookie")
        header_params = [p for p in handler.parameters if p["in"] == "header"]
        cookie_params = [p for p in handler.parameters if p["in"] == "cookie"]
        assert len(header_params) == 1
        assert header_params[0]["name"] == "x-api-key"
        assert len(cookie_params) == 1
        assert cookie_params[0]["name"] == "session_id"


class TestOpenAPIWithMetadata:
    """Tests for generate() with real route metadata."""

    @pytest.mark.asyncio
    async def test_paths_not_empty(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(CatalogService)
        ctx.register_bean(CatalogController)
        await ctx.start()

        registrar = ControllerRegistrar()
        metadata = registrar.collect_route_metadata(ctx)

        gen = OpenAPIGenerator(title="Test", version="1.0")
        spec = gen.generate(route_metadata=metadata)
        assert spec["paths"] != {}

    @pytest.mark.asyncio
    async def test_get_post_put_delete_operations(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(CatalogService)
        ctx.register_bean(CatalogController)
        await ctx.start()

        registrar = ControllerRegistrar()
        metadata = registrar.collect_route_metadata(ctx)

        gen = OpenAPIGenerator(title="Test", version="1.0")
        spec = gen.generate(route_metadata=metadata)
        paths = spec["paths"]

        # GET and DELETE on /{item_id}, GET and POST on /
        item_path = paths["/api/items/{item_id}"]
        assert "get" in item_path
        assert "delete" in item_path
        assert "put" in item_path

        list_path = paths["/api/items/"]
        assert "get" in list_path
        assert "post" in list_path

    @pytest.mark.asyncio
    async def test_path_parameter_in_spec(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(CatalogService)
        ctx.register_bean(CatalogController)
        await ctx.start()

        registrar = ControllerRegistrar()
        metadata = registrar.collect_route_metadata(ctx)

        gen = OpenAPIGenerator(title="Test", version="1.0")
        spec = gen.generate(route_metadata=metadata)

        get_op = spec["paths"]["/api/items/{item_id}"]["get"]
        assert "parameters" in get_op
        param_names = [p["name"] for p in get_op["parameters"]]
        assert "item_id" in param_names

    @pytest.mark.asyncio
    async def test_query_parameter_in_spec(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(CatalogService)
        ctx.register_bean(CatalogController)
        await ctx.start()

        registrar = ControllerRegistrar()
        metadata = registrar.collect_route_metadata(ctx)

        gen = OpenAPIGenerator(title="Test", version="1.0")
        spec = gen.generate(route_metadata=metadata)

        list_op = spec["paths"]["/api/items/"]["get"]
        assert "parameters" in list_op
        page_param = next(p for p in list_op["parameters"] if p["name"] == "page")
        assert page_param["in"] == "query"
        assert page_param["schema"]["type"] == "integer"

    @pytest.mark.asyncio
    async def test_request_body_ref(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(CatalogService)
        ctx.register_bean(CatalogController)
        await ctx.start()

        registrar = ControllerRegistrar()
        metadata = registrar.collect_route_metadata(ctx)

        gen = OpenAPIGenerator(title="Test", version="1.0")
        spec = gen.generate(route_metadata=metadata)

        post_op = spec["paths"]["/api/items/"]["post"]
        assert "requestBody" in post_op
        schema = post_op["requestBody"]["content"]["application/json"]["schema"]
        assert schema["$ref"] == "#/components/schemas/CreateItemRequest"

        # Verify the schema is registered in components
        assert "components" in spec
        assert "CreateItemRequest" in spec["components"]["schemas"]

    @pytest.mark.asyncio
    async def test_info_section(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(CatalogService)
        ctx.register_bean(CatalogController)
        await ctx.start()

        registrar = ControllerRegistrar()
        metadata = registrar.collect_route_metadata(ctx)

        gen = OpenAPIGenerator(title="Catalog API", version="2.0.0", description="Item catalog")
        spec = gen.generate(route_metadata=metadata)

        assert spec["info"]["title"] == "Catalog API"
        assert spec["info"]["version"] == "2.0.0"
        assert spec["info"]["description"] == "Item catalog"

    @pytest.mark.asyncio
    async def test_delete_has_204_response(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(CatalogService)
        ctx.register_bean(CatalogController)
        await ctx.start()

        registrar = ControllerRegistrar()
        metadata = registrar.collect_route_metadata(ctx)

        gen = OpenAPIGenerator(title="Test", version="1.0")
        spec = gen.generate(route_metadata=metadata)

        delete_op = spec["paths"]["/api/items/{item_id}"]["delete"]
        assert "204" in delete_op["responses"]
        assert delete_op["responses"]["204"]["description"] == "No Content"


class TestCreateAppOpenAPI:
    """Test that create_app() wires OpenAPI generation correctly."""

    @pytest.mark.asyncio
    async def test_openapi_json_has_real_paths(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(CatalogService)
        ctx.register_bean(CatalogController)
        await ctx.start()

        app = create_app(title="Test API", version="1.0.0", context=ctx)
        client = TestClient(app)

        response = client.get("/openapi.json")
        assert response.status_code == 200
        spec = response.json()
        assert spec["paths"] != {}
        assert "/api/items/{item_id}" in spec["paths"]

    @pytest.mark.asyncio
    async def test_openapi_json_without_context(self):
        app = create_app(title="Empty API", version="0.1.0")
        client = TestClient(app)

        response = client.get("/openapi.json")
        assert response.status_code == 200
        spec = response.json()
        assert spec["paths"] == {}
        assert spec["info"]["title"] == "Empty API"
