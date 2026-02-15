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
"""Health actuator endpoint."""

from __future__ import annotations

from typing import Any

from pyfly.actuator.health import HealthAggregator


class HealthEndpoint:
    """Exposes aggregated health check results at ``/actuator/health``."""

    def __init__(self, health_aggregator: HealthAggregator) -> None:
        self._aggregator = health_aggregator

    @property
    def endpoint_id(self) -> str:
        return "health"

    @property
    def enabled(self) -> bool:
        return True

    async def handle(self, context: Any = None) -> dict[str, Any]:
        result = await self._aggregator.check()
        return result.to_dict()

    async def get_status_code(self) -> int:
        """Return the HTTP status code based on health state."""
        result = await self._aggregator.check()
        return 503 if result.status == "DOWN" else 200
