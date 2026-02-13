"""Global exception handler — RFC 7807 inspired error responses."""

from __future__ import annotations

import uuid
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from pyfly.kernel.exceptions import (
    BusinessException,
    CircuitBreakerException,
    ConflictException,
    InfrastructureException,
    PyFlyException,
    RateLimitException,
    ResourceNotFoundException,
    SecurityException,
    ServiceUnavailableException,
    ValidationException,
)

# Exception -> HTTP status code mapping (most specific first)
_STATUS_MAP: dict[type, int] = {
    ValidationException: 422,
    ResourceNotFoundException: 404,
    ConflictException: 409,
    SecurityException: 401,
    RateLimitException: 429,
    CircuitBreakerException: 503,
    ServiceUnavailableException: 503,
    BusinessException: 400,
    InfrastructureException: 502,
}


def _get_status_code(exc: Exception) -> int:
    """Map exception type to HTTP status code."""
    for exc_type, status in _STATUS_MAP.items():
        if isinstance(exc, exc_type):
            return status
    return 500


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all exceptions with structured JSON responses."""
    transaction_id = getattr(request.state, "transaction_id", str(uuid.uuid4()))

    if isinstance(exc, PyFlyException):
        status = _get_status_code(exc)
        body: dict[str, Any] = {
            "error": {
                "message": str(exc),
                "code": exc.code or type(exc).__name__,
                "transaction_id": transaction_id,
            }
        }
        if exc.context:
            body["error"]["context"] = exc.context
    else:
        status = 500
        body = {
            "error": {
                "message": "Internal server error",
                "code": "INTERNAL_ERROR",
                "transaction_id": transaction_id,
            }
        }

    return JSONResponse(body, status_code=status)
