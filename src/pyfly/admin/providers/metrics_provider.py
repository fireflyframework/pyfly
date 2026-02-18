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
"""Metrics data provider — reads from Prometheus registry."""

from __future__ import annotations

from typing import Any


class MetricsProvider:
    """Provides metrics data from Prometheus registry."""

    async def get_metric_names(self) -> dict[str, Any]:
        try:
            from prometheus_client import REGISTRY

            names: list[str] = sorted({sample.name for metric in REGISTRY.collect() for sample in metric.samples})
            return {"names": names, "available": True}
        except ImportError:
            return {"names": [], "available": False}

    async def get_metric_detail(self, name: str) -> dict[str, Any]:
        try:
            from prometheus_client import REGISTRY

            measurements: list[dict[str, Any]] = []
            for metric_family in REGISTRY.collect():
                for sample in metric_family.samples:
                    if sample.name == name or sample.name.startswith(name + "_"):
                        measurements.append(
                            {
                                "statistic": sample.name.removeprefix(name).lstrip("_") or "value",
                                "value": sample.value,
                                "tags": dict(sample.labels),
                            }
                        )
            return {"name": name, "measurements": measurements}
        except ImportError:
            return {"name": name, "measurements": [], "available": False}
