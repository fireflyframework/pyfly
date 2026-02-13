"""PyFly web application factory built on Starlette."""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.middleware import Middleware

from pyfly.web.errors import global_exception_handler
from pyfly.web.middleware import TransactionIdMiddleware


def create_app(
    title: str = "PyFly",
    debug: bool = False,
) -> Starlette:
    """Create a Starlette application with PyFly enterprise middleware.

    Includes:
    - Transaction ID propagation
    - Global exception handler (RFC 7807 style)
    """
    middleware = [
        Middleware(TransactionIdMiddleware),
    ]

    app = Starlette(
        debug=debug,
        middleware=middleware,
    )

    # Register global exception handler
    app.add_exception_handler(Exception, global_exception_handler)

    return app
