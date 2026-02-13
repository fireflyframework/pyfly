"""Tests for Swagger UI and ReDoc documentation endpoints."""

from pydantic import BaseModel
from starlette.testclient import TestClient

from pyfly.web.app import create_app
from pyfly.web.router import PyFlyRouter


class UserResponse(BaseModel):
    id: str
    name: str


class TestOpenAPIEndpoint:
    def setup_method(self):
        router = PyFlyRouter(prefix="/api/users", tags=["Users"])

        @router.get("/{user_id}", response_model=UserResponse, summary="Get user")
        async def get_user(request):
            from starlette.responses import JSONResponse
            return JSONResponse({"id": "1", "name": "Alice"})

        self.app = create_app(title="Test API", version="1.0.0", routers=[router])
        self.client = TestClient(self.app)

    def test_openapi_json_served(self):
        resp = self.client.get("/openapi.json")
        assert resp.status_code == 200
        spec = resp.json()
        assert spec["openapi"] == "3.1.0"
        assert spec["info"]["title"] == "Test API"
        assert "/api/users/{user_id}" in spec["paths"]

    def test_swagger_ui_served(self):
        resp = self.client.get("/docs")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "swagger-ui" in resp.text.lower()

    def test_redoc_served(self):
        resp = self.client.get("/redoc")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "redoc" in resp.text.lower()

    def test_no_docs_when_disabled(self):
        app = create_app(title="No Docs", docs_enabled=False)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/openapi.json")
        assert resp.status_code == 404

    def test_no_routers_still_serves_empty_spec(self):
        app = create_app(title="Empty API", version="0.0.1")
        client = TestClient(app)
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        spec = resp.json()
        assert spec["paths"] == {}
