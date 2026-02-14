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
"""Controller discovery, route collection, and request dispatching."""

from __future__ import annotations

import inspect
import typing
from dataclasses import dataclass, field
from typing import Any, get_args, get_origin

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from pyfly.web.params import Body, Cookie, Header, PathVar, QueryParam
from pyfly.web.resolver import ParameterResolver
from pyfly.web.response import handle_return_value

_BINDING_TYPES = {PathVar, QueryParam, Body, Header, Cookie}
_MISSING = object()


def _py_type_to_openapi(t: type) -> str:
    """Map a Python type to an OpenAPI schema type string."""
    if t is int:
        return "integer"
    if t is float:
        return "number"
    if t is bool:
        return "boolean"
    return "string"


@dataclass
class RouteMetadata:
    """Metadata extracted from a single controller handler method."""

    path: str
    http_method: str
    status_code: int
    handler: Any
    handler_name: str
    parameters: list[dict[str, Any]] = field(default_factory=list)
    request_body_model: type | None = None
    return_type: type | None = None


async def _maybe_await(result: Any) -> Any:
    """Await the result if it's a coroutine, otherwise return as-is."""
    if inspect.isawaitable(result):
        return await result
    return result


class ControllerRegistrar:
    """Discovers @rest_controller beans and builds Starlette routes.

    For each controller:
    1. Reads @request_mapping base path from the class
    2. Finds @*_mapping handler methods
    3. Builds a ParameterResolver for each handler
    4. Collects @exception_handler methods
    5. Creates Starlette Route objects that dispatch requests
    """

    def collect_routes(self, ctx: Any) -> list[Route]:
        """Collect all routes from @rest_controller beans in the ApplicationContext."""
        routes: list[Route] = []

        for cls, _reg in ctx.container._registrations.items():
            if getattr(cls, "__pyfly_stereotype__", "") != "rest_controller":
                continue

            instance = ctx.get_bean(cls)
            base_path = getattr(cls, "__pyfly_request_mapping__", "")
            exc_handlers = self._collect_exception_handlers(instance)

            for attr_name in dir(instance):
                method_obj = getattr(instance, attr_name, None)
                if method_obj is None:
                    continue

                mapping = getattr(method_obj, "__pyfly_mapping__", None)
                if mapping is None:
                    continue

                full_path = base_path + mapping["path"]
                http_method = mapping["method"]
                status_code = mapping.get("status_code", 200)

                resolver = ParameterResolver(method_obj)

                handler = self._make_handler(
                    method_obj, resolver, status_code, exc_handlers
                )
                routes.append(Route(full_path, handler, methods=[http_method]))

        return routes

    def collect_route_metadata(self, ctx: Any) -> list[RouteMetadata]:
        """Collect route metadata from all @rest_controller beans for OpenAPI generation."""
        metadata: list[RouteMetadata] = []

        for cls, _reg in ctx.container._registrations.items():
            if getattr(cls, "__pyfly_stereotype__", "") != "rest_controller":
                continue

            instance = ctx.get_bean(cls)
            base_path = getattr(cls, "__pyfly_request_mapping__", "")

            for attr_name in dir(instance):
                method_obj = getattr(instance, attr_name, None)
                if method_obj is None:
                    continue

                mapping = getattr(method_obj, "__pyfly_mapping__", None)
                if mapping is None:
                    continue

                full_path = base_path + mapping["path"]
                http_method = mapping["method"]
                status_code = mapping.get("status_code", 200)

                # Extract parameter metadata and request body model from type hints
                params, body_model = self._extract_param_metadata(method_obj)

                # Extract return type
                hints = typing.get_type_hints(method_obj, include_extras=True)
                return_type = hints.get("return")

                metadata.append(
                    RouteMetadata(
                        path=full_path,
                        http_method=http_method,
                        status_code=status_code,
                        handler=method_obj,
                        handler_name=attr_name,
                        parameters=params,
                        request_body_model=body_model,
                        return_type=return_type,
                    )
                )

        return metadata

    def _extract_param_metadata(
        self, handler: Any
    ) -> tuple[list[dict[str, Any]], type | None]:
        """Extract OpenAPI parameter dicts and request body model from handler type hints."""
        from pydantic import BaseModel

        hints = typing.get_type_hints(handler, include_extras=True)
        sig = inspect.signature(handler)
        params: list[dict[str, Any]] = []
        body_model: type | None = None

        for name, param in sig.parameters.items():
            if name == "self":
                continue

            hint = hints.get(name)
            if hint is None:
                continue

            origin = get_origin(hint)
            if origin not in _BINDING_TYPES:
                continue

            args = get_args(hint)
            inner_type = args[0] if args else str

            default = (
                param.default
                if param.default is not inspect.Parameter.empty
                else _MISSING
            )

            if origin is PathVar:
                params.append({
                    "name": name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": _py_type_to_openapi(inner_type)},
                })
            elif origin is QueryParam:
                p: dict[str, Any] = {
                    "name": name,
                    "in": "query",
                    "required": default is _MISSING,
                    "schema": {"type": _py_type_to_openapi(inner_type)},
                }
                if default is not _MISSING:
                    p["schema"]["default"] = default
                params.append(p)
            elif origin is Header:
                params.append({
                    "name": name.replace("_", "-"),
                    "in": "header",
                    "required": default is _MISSING,
                    "schema": {"type": _py_type_to_openapi(inner_type)},
                })
            elif origin is Cookie:
                params.append({
                    "name": name,
                    "in": "cookie",
                    "required": default is _MISSING,
                    "schema": {"type": _py_type_to_openapi(inner_type)},
                })
            elif origin is Body and isinstance(inner_type, type) and issubclass(inner_type, BaseModel):
                body_model = inner_type

        return params, body_model

    def _collect_exception_handlers(
        self, instance: Any
    ) -> dict[type[Exception], Any]:
        """Collect all @exception_handler methods from a controller instance.

        Handlers are sorted by MRO depth (most specific first) so subclass
        exceptions are matched before their parents.
        """
        handlers: dict[type[Exception], Any] = {}
        for attr_name in dir(instance):
            method = getattr(instance, attr_name, None)
            if method is None:
                continue
            exc_type = getattr(method, "__pyfly_exception_handler__", None)
            if exc_type is not None:
                handlers[exc_type] = method
        return dict(
            sorted(handlers.items(), key=lambda item: len(item[0].__mro__), reverse=True)
        )

    def _make_handler(
        self,
        method: Any,
        resolver: ParameterResolver,
        status_code: int,
        exc_handlers: dict[type[Exception], Any],
    ) -> Any:
        """Create a Starlette-compatible endpoint that dispatches to the controller method."""

        async def endpoint(request: Request) -> Response:
            try:
                kwargs = await resolver.resolve(request)
                result = await _maybe_await(method(**kwargs))
                return handle_return_value(result, status_code)
            except Exception as exc:
                for exc_type, handler in exc_handlers.items():
                    if isinstance(exc, exc_type):
                        result = await _maybe_await(handler(exc))
                        if isinstance(result, tuple) and len(result) == 2:
                            return JSONResponse(result[1], status_code=result[0])
                        return handle_return_value(result)
                raise

        return endpoint
