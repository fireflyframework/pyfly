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
"""Security headers middleware for Starlette."""

from __future__ import annotations

from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from pyfly.web.security_headers import SecurityHeadersConfig


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to every response."""

    def __init__(self, app: Any, config: SecurityHeadersConfig | None = None) -> None:
        super().__init__(app)
        self._config = config or SecurityHeadersConfig()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        cfg = self._config

        response.headers["X-Content-Type-Options"] = cfg.x_content_type_options
        response.headers["X-Frame-Options"] = cfg.x_frame_options
        response.headers["Strict-Transport-Security"] = cfg.strict_transport_security
        response.headers["X-XSS-Protection"] = cfg.x_xss_protection
        response.headers["Referrer-Policy"] = cfg.referrer_policy

        if cfg.content_security_policy is not None:
            response.headers["Content-Security-Policy"] = cfg.content_security_policy
        if cfg.permissions_policy is not None:
            response.headers["Permissions-Policy"] = cfg.permissions_policy

        return response
