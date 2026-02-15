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
"""MetricsFilter — collects HTTP request metrics via prometheus_client."""

from __future__ import annotations

import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram

from pyfly.web.filters import OncePerRequestFilter
from pyfly.web.ports.filter import CallNext


class MetricsFilter(OncePerRequestFilter):
    """Collects HTTP auto-instrumentation metrics.

    Metrics collected:
        - ``http_requests_total`` — counter by method, path, status
        - ``http_request_duration_seconds`` — histogram by method, path
        - ``http_active_requests`` — gauge of in-flight requests
    """

    __pyfly_order__ = -100  # Run early, after RequestContext

    exclude_patterns = ["/actuator/*", "/health", "/ready"]

    def __init__(self) -> None:
        self._requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "path", "status"],
        )
        self._request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "path"],
        )
        self._active_requests = Gauge(
            "http_active_requests",
            "Number of in-flight HTTP requests",
        )

    async def do_filter(self, request: Any, call_next: CallNext) -> Any:
        method = request.method
        path = request.url.path

        self._active_requests.inc()
        start = time.perf_counter()
        try:
            response = await call_next(request)
            status = str(response.status_code)
            return response
        except Exception:
            status = "500"
            raise
        finally:
            duration = time.perf_counter() - start
            self._request_duration.labels(method=method, path=path).observe(duration)
            self._requests_total.labels(method=method, path=path, status=status).inc()
            self._active_requests.dec()
