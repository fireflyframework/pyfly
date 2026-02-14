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
"""Health check system for readiness and liveness probes."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum


class HealthStatus(Enum):
    """Health check status."""

    UP = "UP"
    DOWN = "DOWN"


@dataclass
class HealthResult:
    """Aggregated health check result."""

    status: HealthStatus
    checks: dict[str, HealthStatus] = field(default_factory=dict)


class HealthChecker:
    """Aggregates health checks from multiple components.

    Register health check functions that return True/False for each
    dependency (database, cache, message broker, etc.). The overall
    status is UP only when all checks pass.

    Usage:
        checker = HealthChecker()
        checker.add_check("database", db_health)
        checker.add_check("redis", redis_health)
        result = await checker.check()
    """

    def __init__(self) -> None:
        self._checks: dict[str, Callable[[], Awaitable[bool]]] = {}

    def add_check(self, name: str, check: Callable[[], Awaitable[bool]]) -> None:
        """Register a health check function."""
        self._checks[name] = check

    async def check(self) -> HealthResult:
        """Run all health checks and return aggregated result."""
        checks: dict[str, HealthStatus] = {}
        all_healthy = True

        for name, check_fn in self._checks.items():
            try:
                healthy = await check_fn()
                checks[name] = HealthStatus.UP if healthy else HealthStatus.DOWN
                if not healthy:
                    all_healthy = False
            except Exception:
                checks[name] = HealthStatus.DOWN
                all_healthy = False

        return HealthResult(
            status=HealthStatus.UP if all_healthy else HealthStatus.DOWN,
            checks=checks,
        )
