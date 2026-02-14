"""Controller discovery, route collection, and request dispatching."""

from __future__ import annotations

import inspect
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from pyfly.web.resolver import ParameterResolver
from pyfly.web.response import handle_return_value


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
