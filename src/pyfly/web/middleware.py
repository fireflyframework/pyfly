"""Built-in middleware for PyFly web applications."""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

TRANSACTION_ID_HEADER = "X-Transaction-Id"


class TransactionIdMiddleware(BaseHTTPMiddleware):
    """Injects/propagates X-Transaction-Id on every request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        tx_id = request.headers.get(TRANSACTION_ID_HEADER) or str(uuid.uuid4())
        request.state.transaction_id = tx_id
        response = await call_next(request)
        response.headers[TRANSACTION_ID_HEADER] = tx_id
        return response
