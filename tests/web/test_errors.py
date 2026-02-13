"""Tests for global error handling."""

from starlette.testclient import TestClient

from pyfly.kernel.exceptions import (
    ResourceNotFoundException,
    ValidationException,
)
from pyfly.web.app import create_app


def make_test_app():
    app = create_app(title="test")

    @app.route("/not-found")
    async def not_found(request):
        raise ResourceNotFoundException("Order not found", code="ORDER_NOT_FOUND", context={"id": "123"})

    @app.route("/validation")
    async def validation(request):
        raise ValidationException("Invalid email", code="INVALID_EMAIL")

    @app.route("/ok")
    async def ok(request):
        from starlette.responses import JSONResponse
        return JSONResponse({"status": "ok"})

    return app


class TestGlobalExceptionHandler:
    def setup_method(self):
        self.client = TestClient(make_test_app(), raise_server_exceptions=False)

    def test_not_found_returns_404(self):
        resp = self.client.get("/not-found")
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"]["code"] == "ORDER_NOT_FOUND"
        assert body["error"]["message"] == "Order not found"

    def test_validation_returns_422(self):
        resp = self.client.get("/validation")
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"]["code"] == "INVALID_EMAIL"

    def test_ok_returns_200(self):
        resp = self.client.get("/ok")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_error_has_transaction_id(self):
        resp = self.client.get("/not-found")
        body = resp.json()
        assert "transaction_id" in body["error"]

    def test_unhandled_returns_500(self):
        app = create_app(title="test")

        @app.route("/crash")
        async def crash(request):
            raise RuntimeError("boom")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/crash")
        assert resp.status_code == 500
        body = resp.json()
        assert body["error"]["code"] == "INTERNAL_ERROR"
