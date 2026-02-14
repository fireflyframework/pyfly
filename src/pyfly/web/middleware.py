# Copyright 2026 Firefly Software Solutions Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
