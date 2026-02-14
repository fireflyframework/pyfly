"""Actuator endpoint factories returning Starlette Route lists."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from pyfly.actuator.health import HealthAggregator

if TYPE_CHECKING:
    from pyfly.context.application_context import ApplicationContext


def make_actuator_routes(
    health_aggregator: HealthAggregator,
    context: ApplicationContext | None = None,
) -> list[Route]:
    """Build and return actuator routes.

    Always includes ``/actuator/health``.
    When *context* is provided, also includes ``/actuator/beans``,
    ``/actuator/env``, and ``/actuator/info``.
    """

    # -- /actuator/health ------------------------------------------------
    async def health_endpoint(request: Request) -> JSONResponse:
        result = await health_aggregator.check()
        status_code = 200 if result.status != "DOWN" else 503
        return JSONResponse(result.to_dict(), status_code=status_code)

    routes: list[Route] = [
        Route("/actuator/health", health_endpoint, methods=["GET"]),
    ]

    if context is not None:
        # -- /actuator/beans ---------------------------------------------
        async def beans_endpoint(request: Request) -> JSONResponse:
            beans: dict[str, Any] = {}
            for cls, reg in context.container._registrations.items():
                bean_name = reg.name or cls.__name__
                beans[bean_name] = {
                    "type": f"{cls.__module__}.{cls.__qualname__}",
                    "scope": reg.scope.name,
                    "stereotype": getattr(cls, "__pyfly_stereotype__", "none"),
                }
            return JSONResponse({"beans": beans})

        # -- /actuator/env -----------------------------------------------
        async def env_endpoint(request: Request) -> JSONResponse:
            return JSONResponse({
                "activeProfiles": context.environment.active_profiles,
            })

        # -- /actuator/info ----------------------------------------------
        async def info_endpoint(request: Request) -> JSONResponse:
            info: dict[str, Any] = {
                "app": {
                    "name": context.config.get("app.name", ""),
                    "version": context.config.get("app.version", ""),
                    "description": context.config.get("app.description", ""),
                },
            }
            return JSONResponse(info)

        routes.extend([
            Route("/actuator/beans", beans_endpoint, methods=["GET"]),
            Route("/actuator/env", env_endpoint, methods=["GET"]),
            Route("/actuator/info", info_endpoint, methods=["GET"]),
        ])

    return routes
