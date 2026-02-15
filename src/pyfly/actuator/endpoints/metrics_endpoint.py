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
"""Metrics actuator endpoint — stub for future Prometheus integration."""

from __future__ import annotations

from typing import Any


class MetricsEndpoint:
    """Stub endpoint at ``/actuator/metrics`` for future metrics integration.

    Returns basic metadata.  Will be extended for Prometheus/OpenTelemetry.
    """

    @property
    def endpoint_id(self) -> str:
        return "metrics"

    @property
    def enabled(self) -> bool:
        return False  # Disabled by default until a metrics backend is integrated

    async def handle(self, context: Any = None) -> dict[str, Any]:
        return {
            "names": [],
            "message": "Metrics endpoint stub. Configure a metrics backend to populate.",
        }
