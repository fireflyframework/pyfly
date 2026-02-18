"""Tests for RequestContextFilter — sets up RequestContext per HTTP request."""

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from pyfly.context.request_context import RequestContext
from pyfly.web.adapters.starlette.filter_chain import WebFilterChainMiddleware
from pyfly.web.adapters.starlette.filters.request_context_filter import (
    RequestContextFilter,
)


async def context_endpoint(request: Request) -> JSONResponse:
    """Test endpoint that reads the RequestContext."""
    ctx = RequestContext.current()
    return JSONResponse(
        {
            "has_context": ctx is not None,
            "request_id": ctx.request_id if ctx else None,
        }
    )


@pytest.fixture
def app():
    filters = [RequestContextFilter()]
    routes = [
        Route("/test", context_endpoint),
    ]
    app = Starlette(
        routes=routes,
        middleware=[Middleware(WebFilterChainMiddleware, filters=filters)],
    )
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestRequestContextFilter:
    def test_context_is_set_during_request(self, client):
        response = client.get("/test")
        assert response.status_code == 200
        data = response.json()
        assert data["has_context"] is True
        assert data["request_id"] is not None

    def test_each_request_gets_unique_id(self, client):
        r1 = client.get("/test").json()["request_id"]
        r2 = client.get("/test").json()["request_id"]
        assert r1 != r2

    def test_uses_x_request_id_header_if_present(self, client):
        response = client.get("/test", headers={"X-Request-Id": "custom-123"})
        data = response.json()
        assert data["request_id"] == "custom-123"

    def test_context_cleared_after_request(self, client):
        client.get("/test")
        assert RequestContext.current() is None
