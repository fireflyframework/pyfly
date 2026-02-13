"""PyFly web application factory built on Starlette."""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Route

from pyfly.web.docs import make_openapi_endpoint, make_redoc_endpoint, make_swagger_ui_endpoint
from pyfly.web.errors import global_exception_handler
from pyfly.web.middleware import TransactionIdMiddleware
from pyfly.web.openapi import OpenAPIGenerator
from pyfly.web.router import PyFlyRouter


def create_app(
    title: str = "PyFly",
    version: str = "0.1.0",
    description: str = "",
    debug: bool = False,
    routers: list[PyFlyRouter] | None = None,
    docs_enabled: bool = True,
) -> Starlette:
    """Create a Starlette application with PyFly enterprise middleware.

    Includes:
    - Transaction ID propagation
    - Global exception handler (RFC 7807 style)
    - OpenAPI spec, Swagger UI, and ReDoc (when docs_enabled)
    """
    middleware = [
        Middleware(TransactionIdMiddleware),
    ]

    routes: list[Route] = []

    # Mount router routes
    all_routers = routers or []

    # Generate OpenAPI spec and doc routes
    if docs_enabled:
        generator = OpenAPIGenerator(
            title=title,
            version=version,
            routers=all_routers,
            description=description,
        )
        spec = generator.generate()

        routes.extend([
            Route("/openapi.json", make_openapi_endpoint(spec)),
            Route("/docs", make_swagger_ui_endpoint(title)),
            Route("/redoc", make_redoc_endpoint(title)),
        ])

    # Add router routes
    for router in all_routers:
        for meta in router.get_route_metadata():
            routes.append(Route(meta.path, meta.handler, methods=[meta.method]))

    app = Starlette(
        debug=debug,
        middleware=middleware,
        routes=routes,
    )

    # Register global exception handler
    app.add_exception_handler(Exception, global_exception_handler)

    return app
