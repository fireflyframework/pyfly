"""Request logging middleware -- logs method, path, status, and duration."""

from __future__ import annotations

import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger("pyfly.web")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs HTTP method, path, status code, and duration for each request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        tx_id = getattr(request.state, "transaction_id", None)

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "http_request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
                transaction_id=tx_id,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            transaction_id=tx_id,
        )
        return response
