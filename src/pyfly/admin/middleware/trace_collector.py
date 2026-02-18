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
"""HTTP trace collector -- WebFilter that captures request/response metadata."""

from __future__ import annotations

import time
from collections import deque
from datetime import UTC, datetime
from typing import Any

from pyfly.web.filters import OncePerRequestFilter
from pyfly.web.ports.filter import CallNext


class TraceCollectorFilter(OncePerRequestFilter):
    """Captures HTTP request/response traces for the admin dashboard.

    Stores traces in a fixed-size ring buffer (deque with maxlen).
    Excludes admin and actuator paths by default.
    """

    exclude_patterns = ["/admin/*", "/actuator/*"]

    def __init__(self, max_traces: int = 500) -> None:
        self._traces: deque[dict[str, Any]] = deque(maxlen=max_traces)

    async def do_filter(self, request: Any, call_next: CallNext) -> Any:
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        self._traces.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            }
        )
        return response

    def get_traces(self) -> list[dict[str, Any]]:
        return list(self._traces)

    def clear_traces(self) -> None:
        self._traces.clear()
