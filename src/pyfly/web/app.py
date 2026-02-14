"""PyFly web application factory built on Starlette."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Route

from pyfly.web.controller import ControllerRegistrar
from pyfly.web.docs import make_openapi_endpoint, make_redoc_endpoint, make_swagger_ui_endpoint
from pyfly.web.errors import global_exception_handler
from pyfly.web.middleware import TransactionIdMiddleware
from pyfly.web.request_logger import RequestLoggingMiddleware

if TYPE_CHECKING:
    from pyfly.context.application_context import ApplicationContext


def create_app(
    title: str = "PyFly",
    version: str = "0.1.0",
    description: str = "",
    debug: bool = False,
    context: ApplicationContext | None = None,
    docs_enabled: bool = True,
    extra_routes: list[Route] | None = None,
) -> Starlette:
    """Create a Starlette application with PyFly enterprise middleware.

    When ``context`` is provided, auto-discovers all ``@rest_controller`` beans
    and mounts their routes.

    Includes:
    - Transaction ID propagation
    - Global exception handler (RFC 7807 style)
    - OpenAPI spec, Swagger UI, and ReDoc (when docs_enabled)
    """
    middleware = [
        Middleware(TransactionIdMiddleware),
        Middleware(RequestLoggingMiddleware),
    ]

    routes: list[Route] = []

    # Auto-discover controller routes from ApplicationContext
    if context is not None:
        registrar = ControllerRegistrar()
        routes.extend(registrar.collect_routes(context))

    # Append caller-supplied routes (e.g. test helpers)
    if extra_routes:
        routes.extend(extra_routes)

    # Generate OpenAPI spec and doc routes
    if docs_enabled:
        spec: dict[str, Any] = {
            "openapi": "3.1.0",
            "info": {"title": title, "version": version},
            "paths": {},
        }
        if description:
            spec["info"]["description"] = description

        routes.extend([
            Route("/openapi.json", make_openapi_endpoint(spec)),
            Route("/docs", make_swagger_ui_endpoint(title)),
            Route("/redoc", make_redoc_endpoint(title)),
        ])

    app = Starlette(
        debug=debug,
        middleware=middleware,
        routes=routes,
    )

    # Register global exception handler
    app.add_exception_handler(Exception, global_exception_handler)

    return app
