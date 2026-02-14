"""Tests for Swagger UI and ReDoc doc endpoints."""

import pytest
from starlette.testclient import TestClient

from pyfly.context.application_context import ApplicationContext
from pyfly.core.config import Config
from pyfly.web.app import create_app


class TestDocEndpoints:
    @pytest.mark.asyncio
    async def test_openapi_json(self):
        ctx = ApplicationContext(Config({}))
        await ctx.start()
        app = create_app(context=ctx)
        client = TestClient(app)
        response = client.get("/openapi.json")
        assert response.status_code == 200
        spec = response.json()
        assert spec["openapi"] == "3.1.0"

    @pytest.mark.asyncio
    async def test_swagger_ui(self):
        ctx = ApplicationContext(Config({}))
        await ctx.start()
        app = create_app(title="Test", context=ctx)
        client = TestClient(app)
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger-ui" in response.text

    @pytest.mark.asyncio
    async def test_redoc(self):
        ctx = ApplicationContext(Config({}))
        await ctx.start()
        app = create_app(title="Test", context=ctx)
        client = TestClient(app)
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text

    @pytest.mark.asyncio
    async def test_docs_disabled(self):
        ctx = ApplicationContext(Config({}))
        await ctx.start()
        app = create_app(context=ctx, docs_enabled=False)
        client = TestClient(app)
        response = client.get("/docs")
        assert response.status_code == 404
