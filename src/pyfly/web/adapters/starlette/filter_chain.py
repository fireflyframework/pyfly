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
"""WebFilterChainMiddleware — single Starlette middleware wrapping all WebFilters."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from pyfly.web.ports.filter import CallNext, WebFilter


class WebFilterChainMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that executes a sorted chain of :class:`WebFilter` instances.

    Wraps all filters inside a single ``BaseHTTPMiddleware`` to avoid the
    per-middleware task-context overhead.  Filters are executed in the order
    provided (should already be sorted by ``@order``).

    Each filter's ``should_not_filter()`` is checked before invocation — if it
    returns ``True``, the filter is skipped and the next one in the chain runs.
    """

    def __init__(self, app: Any, filters: Sequence[WebFilter] = ()) -> None:
        super().__init__(app)
        self._filters = list(filters)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        chain: CallNext = call_next  # type: ignore[assignment]

        # Build the chain from right to left (last filter wraps call_next,
        # first filter is the outermost wrapper).
        for f in reversed(self._filters):
            chain = _wrap(f, chain)

        return cast(Response, await chain(request))


def _wrap(web_filter: WebFilter, next_call: CallNext) -> CallNext:
    """Create a closure that conditionally invokes *web_filter*."""

    async def _inner(request: Request) -> Response:
        if web_filter.should_not_filter(request):
            return cast(Response, await next_call(request))
        return cast(Response, await web_filter.do_filter(request, next_call))

    return _inner
