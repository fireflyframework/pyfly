"""Tests for OpenAPI 3.1 schema generation."""
from pydantic import BaseModel

from pyfly.web.openapi import OpenAPIGenerator
from pyfly.web.router import PyFlyRouter


class ItemResponse(BaseModel):
    id: str
    name: str
    price: float

class CreateItemRequest(BaseModel):
    name: str
    price: float


class TestOpenAPIGenerator:
    def _make_router(self) -> PyFlyRouter:
        router = PyFlyRouter(prefix="/api/items", tags=["Items"])

        @router.get("/", summary="List all items")
        async def list_items(request): pass

        @router.get("/{item_id}", response_model=ItemResponse, summary="Get an item by ID")
        async def get_item(request): pass

        @router.post("/", request_model=CreateItemRequest, response_model=ItemResponse,
                     status_code=201, summary="Create a new item")
        async def create_item(request): pass

        @router.delete("/{item_id}", status_code=204, summary="Delete an item")
        async def delete_item(request): pass

        return router

    def test_generates_valid_openapi_structure(self):
        router = self._make_router()
        gen = OpenAPIGenerator(title="Test API", version="1.0.0", routers=[router])
        spec = gen.generate()
        assert spec["openapi"] == "3.1.0"
        assert spec["info"]["title"] == "Test API"
        assert spec["info"]["version"] == "1.0.0"
        assert "paths" in spec

    def test_generates_paths_for_all_routes(self):
        router = self._make_router()
        gen = OpenAPIGenerator(title="Test API", version="1.0.0", routers=[router])
        spec = gen.generate()
        paths = spec["paths"]
        assert "/api/items/" in paths
        assert "/api/items/{item_id}" in paths

    def test_get_operation_has_summary(self):
        router = self._make_router()
        gen = OpenAPIGenerator(title="Test API", version="1.0.0", routers=[router])
        spec = gen.generate()
        get_op = spec["paths"]["/api/items/{item_id}"]["get"]
        assert get_op["summary"] == "Get an item by ID"
        assert get_op["tags"] == ["Items"]

    def test_post_has_request_body(self):
        router = self._make_router()
        gen = OpenAPIGenerator(title="Test API", version="1.0.0", routers=[router])
        spec = gen.generate()
        post_op = spec["paths"]["/api/items/"]["post"]
        assert "requestBody" in post_op
        req_schema = post_op["requestBody"]["content"]["application/json"]["schema"]
        assert "$ref" in req_schema

    def test_response_model_in_schema(self):
        router = self._make_router()
        gen = OpenAPIGenerator(title="Test API", version="1.0.0", routers=[router])
        spec = gen.generate()
        get_op = spec["paths"]["/api/items/{item_id}"]["get"]
        assert "content" in get_op["responses"]["200"]

    def test_delete_has_204_response(self):
        router = self._make_router()
        gen = OpenAPIGenerator(title="Test API", version="1.0.0", routers=[router])
        spec = gen.generate()
        delete_op = spec["paths"]["/api/items/{item_id}"]["delete"]
        assert "204" in delete_op["responses"]

    def test_path_params_extracted(self):
        router = self._make_router()
        gen = OpenAPIGenerator(title="Test API", version="1.0.0", routers=[router])
        spec = gen.generate()
        get_op = spec["paths"]["/api/items/{item_id}"]["get"]
        params = get_op.get("parameters", [])
        param_names = [p["name"] for p in params]
        assert "item_id" in param_names

    def test_components_schemas_generated(self):
        router = self._make_router()
        gen = OpenAPIGenerator(title="Test API", version="1.0.0", routers=[router])
        spec = gen.generate()
        schemas = spec.get("components", {}).get("schemas", {})
        assert "ItemResponse" in schemas
        assert "CreateItemRequest" in schemas

    def test_multiple_routers(self):
        router1 = PyFlyRouter(prefix="/api/items", tags=["Items"])
        router2 = PyFlyRouter(prefix="/api/users", tags=["Users"])
        @router1.get("/", summary="List items")
        async def list_items(request): pass
        @router2.get("/", summary="List users")
        async def list_users(request): pass
        gen = OpenAPIGenerator(title="Multi", version="1.0.0", routers=[router1, router2])
        spec = gen.generate()
        assert "/api/items/" in spec["paths"]
        assert "/api/users/" in spec["paths"]

    def test_no_components_when_no_models(self):
        router = PyFlyRouter(prefix="/api", tags=["Test"])
        @router.get("/health", summary="Health check")
        async def health(request): pass
        gen = OpenAPIGenerator(title="Simple", version="1.0.0", routers=[router])
        spec = gen.generate()
        assert "components" not in spec
