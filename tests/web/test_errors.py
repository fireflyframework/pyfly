"""Tests for global error handling."""

from starlette.testclient import TestClient

from pyfly.kernel.exceptions import (
    BadGatewayException,
    BulkheadException,
    DegradedServiceException,
    ForbiddenException,
    GatewayTimeoutException,
    GoneException,
    LockedResourceException,
    MethodNotAllowedException,
    NotImplementedException,
    OperationTimeoutException,
    PayloadTooLargeException,
    PreconditionFailedException,
    QuotaExceededException,
    ResourceNotFoundException,
    UnauthorizedException,
    UnsupportedMediaTypeException,
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


class TestExpandedStatusMapping:
    """Verify that each new exception type maps to the correct HTTP status code."""

    def setup_method(self):
        app = create_app(title="test")

        @app.route("/unauthorized")
        async def unauthorized(request):
            raise UnauthorizedException("not authenticated")

        @app.route("/forbidden")
        async def forbidden(request):
            raise ForbiddenException("access denied")

        @app.route("/gone")
        async def gone(request):
            raise GoneException("resource deleted")

        @app.route("/precondition-failed")
        async def precondition_failed(request):
            raise PreconditionFailedException("etag mismatch")

        @app.route("/locked")
        async def locked(request):
            raise LockedResourceException("resource locked")

        @app.route("/method-not-allowed")
        async def method_not_allowed(request):
            raise MethodNotAllowedException("POST not allowed")

        @app.route("/unsupported-media-type")
        async def unsupported_media_type(request):
            raise UnsupportedMediaTypeException("use application/json")

        @app.route("/payload-too-large")
        async def payload_too_large(request):
            raise PayloadTooLargeException("max 10MB")

        @app.route("/operation-timeout")
        async def operation_timeout(request):
            raise OperationTimeoutException("timed out")

        @app.route("/bad-gateway")
        async def bad_gateway(request):
            raise BadGatewayException("upstream error")

        @app.route("/gateway-timeout")
        async def gateway_timeout(request):
            raise GatewayTimeoutException("upstream timeout")

        @app.route("/not-implemented")
        async def not_implemented(request):
            raise NotImplementedException("coming soon")

        @app.route("/bulkhead")
        async def bulkhead(request):
            raise BulkheadException("capacity full")

        @app.route("/degraded")
        async def degraded(request):
            raise DegradedServiceException("running degraded")

        @app.route("/quota-exceeded")
        async def quota_exceeded(request):
            raise QuotaExceededException("quota used up")

        self.client = TestClient(app, raise_server_exceptions=False)

    def test_unauthorized_returns_401(self):
        resp = self.client.get("/unauthorized")
        assert resp.status_code == 401

    def test_forbidden_returns_403(self):
        resp = self.client.get("/forbidden")
        assert resp.status_code == 403

    def test_gone_returns_410(self):
        resp = self.client.get("/gone")
        assert resp.status_code == 410

    def test_precondition_failed_returns_412(self):
        resp = self.client.get("/precondition-failed")
        assert resp.status_code == 412

    def test_locked_resource_returns_423(self):
        resp = self.client.get("/locked")
        assert resp.status_code == 423

    def test_method_not_allowed_returns_405(self):
        resp = self.client.get("/method-not-allowed")
        assert resp.status_code == 405

    def test_unsupported_media_type_returns_415(self):
        resp = self.client.get("/unsupported-media-type")
        assert resp.status_code == 415

    def test_payload_too_large_returns_413(self):
        resp = self.client.get("/payload-too-large")
        assert resp.status_code == 413

    def test_operation_timeout_returns_504(self):
        resp = self.client.get("/operation-timeout")
        assert resp.status_code == 504

    def test_bad_gateway_returns_502(self):
        resp = self.client.get("/bad-gateway")
        assert resp.status_code == 502

    def test_gateway_timeout_returns_504(self):
        resp = self.client.get("/gateway-timeout")
        assert resp.status_code == 504

    def test_not_implemented_returns_501(self):
        resp = self.client.get("/not-implemented")
        assert resp.status_code == 501

    def test_bulkhead_returns_503(self):
        resp = self.client.get("/bulkhead")
        assert resp.status_code == 503

    def test_degraded_service_returns_503(self):
        resp = self.client.get("/degraded")
        assert resp.status_code == 503

    def test_quota_exceeded_returns_429(self):
        resp = self.client.get("/quota-exceeded")
        assert resp.status_code == 429

    def test_response_contains_timestamp(self):
        resp = self.client.get("/unauthorized")
        body = resp.json()
        assert "timestamp" in body["error"]

    def test_response_contains_status(self):
        resp = self.client.get("/forbidden")
        body = resp.json()
        assert body["error"]["status"] == 403

    def test_response_contains_path(self):
        resp = self.client.get("/gone")
        body = resp.json()
        assert body["error"]["path"] == "/gone"
