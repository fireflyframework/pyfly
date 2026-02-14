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
"""Framework-agnostic actuator data providers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyfly.actuator.health import HealthAggregator

if TYPE_CHECKING:
    from pyfly.context.application_context import ApplicationContext


async def get_health_data(health_aggregator: HealthAggregator) -> tuple[dict[str, Any], int]:
    """Return health check data and HTTP status code."""
    result = await health_aggregator.check()
    status_code = 200 if result.status != "DOWN" else 503
    return result.to_dict(), status_code


def get_beans_data(context: ApplicationContext) -> dict[str, Any]:
    """Return bean registry data."""
    beans: dict[str, Any] = {}
    for cls, reg in context.container._registrations.items():
        bean_name = reg.name or cls.__name__
        beans[bean_name] = {
            "type": f"{cls.__module__}.{cls.__qualname__}",
            "scope": reg.scope.name,
            "stereotype": getattr(cls, "__pyfly_stereotype__", "none"),
        }
    return {"beans": beans}


def get_env_data(context: ApplicationContext) -> dict[str, Any]:
    """Return environment data."""
    return {"activeProfiles": context.environment.active_profiles}


def get_info_data(context: ApplicationContext) -> dict[str, Any]:
    """Return application info data."""
    return {
        "app": {
            "name": context.config.get("pyfly.app.name", ""),
            "version": context.config.get("pyfly.app.version", ""),
            "description": context.config.get("pyfly.app.description", ""),
        },
    }


def make_actuator_routes(
    health_aggregator: HealthAggregator,
    context: ApplicationContext | None = None,
) -> Any:
    """Build actuator routes using the Starlette adapter.

    This is a convenience function that delegates to the Starlette adapter.
    """
    from pyfly.actuator.adapters.starlette import make_starlette_actuator_routes

    return make_starlette_actuator_routes(health_aggregator, context)
