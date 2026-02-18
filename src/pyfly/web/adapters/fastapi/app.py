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
"""PyFly web application factory built on FastAPI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI
from starlette.middleware import Middleware

from pyfly.container.ordering import get_order
from pyfly.web.adapters.fastapi.controller import FastAPIControllerRegistrar
from pyfly.web.adapters.fastapi.errors import register_exception_handlers
from pyfly.web.adapters.starlette.filter_chain import WebFilterChainMiddleware
from pyfly.web.adapters.starlette.filters import (
    RequestLoggingFilter,
    SecurityHeadersFilter,
    TransactionIdFilter,
)
from pyfly.web.ports.filter import WebFilter

if TYPE_CHECKING:
    from pyfly.context.application_context import ApplicationContext
    from pyfly.web.cors import CORSConfig


def create_app(
    title: str = "PyFly",
    version: str = "0.1.0",
    description: str = "",
    debug: bool = False,
    context: ApplicationContext | None = None,
    docs_enabled: bool = True,
    cors: CORSConfig | None = None,
    lifespan: object | None = None,
) -> FastAPI:
    """Create a FastAPI application with PyFly enterprise middleware.

    When ``context`` is provided, auto-discovers all ``@rest_controller`` beans
    and mounts their routes.  Also auto-discovers user ``WebFilter`` beans.

    FastAPI provides built-in OpenAPI docs (Swagger UI at ``/docs``, ReDoc at
    ``/redoc``), so no custom OpenAPI generator is needed.

    Includes:
    - WebFilter chain (transaction ID, request logging, security headers, + user filters)
    - Global exception handler (RFC 7807 style)
    - Built-in Swagger UI and ReDoc (when docs_enabled)
    - CORS support (when cors is provided)
    """
    # --- Build the WebFilter chain ---
    filters: list[WebFilter] = [
        TransactionIdFilter(),
        RequestLoggingFilter(),
        SecurityHeadersFilter(),
    ]

    # Auto-discover user WebFilter beans from context
    if context is not None:
        for _cls, reg in context.container._registrations.items():
            if (
                reg.instance is not None
                and isinstance(reg.instance, WebFilter)
                and not isinstance(
                    reg.instance,
                    (TransactionIdFilter, RequestLoggingFilter, SecurityHeadersFilter),
                )
            ):
                filters.append(reg.instance)

    # Sort all filters by @order (built-in filters use HIGHEST_PRECEDENCE offsets)
    filters.sort(key=lambda f: get_order(type(f)))

    middleware: list[Middleware] = [
        Middleware(WebFilterChainMiddleware, filters=filters),
    ]

    if cors is not None:
        from starlette.middleware.cors import CORSMiddleware

        middleware.append(
            Middleware(
                CORSMiddleware,
                allow_origins=cors.allowed_origins,
                allow_methods=cors.allowed_methods,
                allow_headers=cors.allowed_headers,
                allow_credentials=cors.allow_credentials,
                expose_headers=cors.exposed_headers,
                max_age=cors.max_age,
            )
        )

    # Configure OpenAPI docs URLs (None disables them)
    docs_url = "/docs" if docs_enabled else None
    redoc_url = "/redoc" if docs_enabled else None
    openapi_url = "/openapi.json" if docs_enabled else None

    app = FastAPI(
        title=title,
        version=version,
        description=description,
        debug=debug,
        middleware=middleware,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,  # type: ignore[arg-type]
    )

    # Auto-discover and register controller routes from ApplicationContext
    if context is not None:
        registrar = FastAPIControllerRegistrar()
        registrar.register_controllers(app, context)

    # Register global exception handler
    register_exception_handlers(app)

    # Store metadata for startup logging
    app.state.pyfly_docs_enabled = docs_enabled

    return app
