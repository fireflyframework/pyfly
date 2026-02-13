"""Tests for PyFlyRouter with OpenAPI metadata collection."""
import pytest
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.testclient import TestClient
from pyfly.web.router import PyFlyRouter, RouteMetadata


class ItemResponse(BaseModel):
    id: str
    name: str

class CreateItemRequest(BaseModel):
    name: str
    price: float


class TestRouteMetadataCollection:
    def test_get_route_collects_metadata(self):
        router = PyFlyRouter(prefix="/api/items", tags=["Items"])
        @router.get("/{item_id}", response_model=ItemResponse, summary="Get an item")
        async def get_item(request: Request) -> JSONResponse:
            return JSONResponse({"id": "1", "name": "Widget"})
        routes = router.get_route_metadata()
        assert len(routes) == 1
        meta = routes[0]
        assert meta.path == "/api/items/{item_id}"
        assert meta.method == "GET"
        assert meta.response_model is ItemResponse
        assert meta.summary == "Get an item"
        assert meta.tags == ["Items"]

    def test_post_route_collects_request_model(self):
        router = PyFlyRouter(prefix="/api/items", tags=["Items"])
        @router.post("/", request_model=CreateItemRequest, response_model=ItemResponse,
                     status_code=201, summary="Create an item")
        async def create_item(request: Request) -> JSONResponse:
            return JSONResponse({"id": "1", "name": "Widget"}, status_code=201)
        routes = router.get_route_metadata()
        assert len(routes) == 1
        meta = routes[0]
        assert meta.path == "/api/items/"
        assert meta.method == "POST"
        assert meta.request_model is CreateItemRequest
        assert meta.response_model is ItemResponse
        assert meta.status_code == 201

    def test_multiple_routes(self):
        router = PyFlyRouter(prefix="/api/items", tags=["Items"])
        @router.get("/", summary="List items")
        async def list_items(request: Request) -> JSONResponse:
            return JSONResponse([])
        @router.get("/{item_id}", response_model=ItemResponse, summary="Get item")
        async def get_item(request: Request) -> JSONResponse:
            return JSONResponse({"id": "1", "name": "Widget"})
        @router.delete("/{item_id}", status_code=204, summary="Delete item")
        async def delete_item(request: Request) -> JSONResponse:
            return JSONResponse(None, status_code=204)
        routes = router.get_route_metadata()
        assert len(routes) == 3

    def test_router_routes_work(self):
        from starlette.applications import Starlette
        router = PyFlyRouter(prefix="/api/items", tags=["Items"])
        @router.get("/{item_id}", response_model=ItemResponse, summary="Get item")
        async def get_item(request: Request) -> JSONResponse:
            return JSONResponse({"id": "1", "name": "Widget"})
        mount = router.to_starlette_routes()
        app = Starlette(routes=[mount])
        client = TestClient(app)
        resp = client.get("/api/items/1")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Widget"

    def test_put_and_patch_routes(self):
        router = PyFlyRouter(prefix="/api", tags=["API"])
        @router.put("/{id}", summary="Replace")
        async def replace(request: Request) -> JSONResponse:
            return JSONResponse({"ok": True})
        @router.patch("/{id}", summary="Update")
        async def update(request: Request) -> JSONResponse:
            return JSONResponse({"ok": True})
        routes = router.get_route_metadata()
        methods = {r.method for r in routes}
        assert methods == {"PUT", "PATCH"}
