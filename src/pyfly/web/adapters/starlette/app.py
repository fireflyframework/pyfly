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
"""PyFly web application factory built on Starlette."""

from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Route

from pyfly.container.ordering import get_order
from pyfly.web.adapters.starlette.controller import ControllerRegistrar
from pyfly.web.adapters.starlette.docs import (
    make_openapi_endpoint,
    make_redoc_endpoint,
    make_swagger_ui_endpoint,
)
from pyfly.web.adapters.starlette.errors import global_exception_handler
from pyfly.web.adapters.starlette.filter_chain import WebFilterChainMiddleware
from pyfly.web.adapters.starlette.filters import (
    RequestLoggingFilter,
    SecurityHeadersFilter,
    TransactionIdFilter,
)
from pyfly.web.openapi import OpenAPIGenerator
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
    extra_routes: list[Route] | None = None,
    actuator_enabled: bool = False,
    cors: CORSConfig | None = None,
    lifespan: object | None = None,
) -> Starlette:
    """Create a Starlette application with PyFly enterprise middleware.

    When ``context`` is provided, auto-discovers all ``@rest_controller`` beans
    and mounts their routes.  Also auto-discovers user ``WebFilter`` and
    ``ActuatorEndpoint`` beans.

    Includes:
    - WebFilter chain (transaction ID, request logging, security headers, + user filters)
    - Global exception handler (RFC 7807 style)
    - OpenAPI spec, Swagger UI, and ReDoc (when docs_enabled)
    - Actuator endpoints (when actuator_enabled)
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

    routes: list[Route] = []
    registrar = ControllerRegistrar()

    # Auto-discover controller routes from ApplicationContext
    if context is not None:
        routes.extend(registrar.collect_routes(context))

    # Append caller-supplied routes (e.g. test helpers)
    if extra_routes:
        routes.extend(extra_routes)

    # Mount actuator endpoints when enabled
    if actuator_enabled:
        from pyfly.actuator.adapters.starlette import make_starlette_actuator_routes
        from pyfly.actuator.endpoints.beans_endpoint import BeansEndpoint
        from pyfly.actuator.endpoints.env_endpoint import EnvEndpoint
        from pyfly.actuator.endpoints.health_endpoint import HealthEndpoint
        from pyfly.actuator.endpoints.info_endpoint import InfoEndpoint
        from pyfly.actuator.endpoints.loggers_endpoint import LoggersEndpoint
        from pyfly.actuator.endpoints.metrics_endpoint import MetricsEndpoint
        from pyfly.actuator.health import HealthAggregator, HealthIndicator
        from pyfly.actuator.registry import ActuatorRegistry

        agg = HealthAggregator()

        # Auto-discover HealthIndicator beans from context
        if context is not None:
            for cls, reg in context.container._registrations.items():
                if reg.instance is not None and isinstance(reg.instance, HealthIndicator):
                    indicator_name = reg.name or cls.__name__
                    agg.add_indicator(indicator_name, reg.instance)

        config = context.config if context is not None else None
        registry = ActuatorRegistry(config=config)

        # Register built-in endpoints
        registry.register(HealthEndpoint(agg))
        if context is not None:
            registry.register(BeansEndpoint(context))
            registry.register(EnvEndpoint(context))
            registry.register(InfoEndpoint(context))
        registry.register(LoggersEndpoint())
        registry.register(MetricsEndpoint())

        # Auto-discover custom ActuatorEndpoint beans from context
        if context is not None:
            registry.discover_from_context(context)

        routes.extend(make_starlette_actuator_routes(registry))

    # Collect route metadata (used for OpenAPI and startup logging)
    route_metadata = registrar.collect_route_metadata(context) if context is not None else []

    # Generate OpenAPI spec and doc routes
    if docs_enabled:
        generator = OpenAPIGenerator(title=title, version=version, description=description)
        spec = generator.generate(route_metadata or None)

        routes.extend([
            Route("/openapi.json", make_openapi_endpoint(spec)),
            Route("/docs", make_swagger_ui_endpoint(title)),
            Route("/redoc", make_redoc_endpoint(title)),
        ])

    app = Starlette(
        debug=debug,
        middleware=middleware,
        routes=routes,
        lifespan=lifespan,
    )

    # Store metadata for startup logging
    app.state.pyfly_route_metadata = route_metadata
    app.state.pyfly_docs_enabled = docs_enabled

    # Register global exception handler
    app.add_exception_handler(Exception, global_exception_handler)

    return app
