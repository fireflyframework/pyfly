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
"""Starlette adapter for actuator endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from pyfly.actuator.endpoints import get_beans_data, get_env_data, get_health_data, get_info_data
from pyfly.actuator.health import HealthAggregator

if TYPE_CHECKING:
    from pyfly.context.application_context import ApplicationContext


def make_starlette_actuator_routes(
    health_aggregator: HealthAggregator,
    context: ApplicationContext | None = None,
) -> list[Route]:
    """Build Starlette Route objects for actuator endpoints."""

    async def health_endpoint(request: Request) -> JSONResponse:
        data, status_code = await get_health_data(health_aggregator)
        return JSONResponse(data, status_code=status_code)

    routes: list[Route] = [
        Route("/actuator/health", health_endpoint, methods=["GET"]),
    ]

    if context is not None:
        async def beans_endpoint(request: Request) -> JSONResponse:
            return JSONResponse(get_beans_data(context))

        async def env_endpoint(request: Request) -> JSONResponse:
            return JSONResponse(get_env_data(context))

        async def info_endpoint(request: Request) -> JSONResponse:
            return JSONResponse(get_info_data(context))

        routes.extend([
            Route("/actuator/beans", beans_endpoint, methods=["GET"]),
            Route("/actuator/env", env_endpoint, methods=["GET"]),
            Route("/actuator/info", info_endpoint, methods=["GET"]),
        ])

    return routes
