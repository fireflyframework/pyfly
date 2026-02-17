"""Tests for @controller stereotype discovery and Request injection."""

import pytest
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.testclient import TestClient

from pyfly.container.stereotypes import controller, service
from pyfly.context.application_context import ApplicationContext
from pyfly.core.config import Config
from pyfly.web.adapters.starlette.controller import ControllerRegistrar
from pyfly.web.adapters.starlette.resolver import ParameterResolver
from pyfly.web.mappings import get_mapping, request_mapping
from pyfly.web.params import PathVar


@service
class GreetingService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"


@controller
@request_mapping("/pages")
class PageController:
    def __init__(self, greeting_service: GreetingService) -> None:
        self._svc = greeting_service

    @get_mapping("/")
    async def home(self, request: Request):
        return HTMLResponse(f"<h1>{self._svc.greet('World')}</h1>")

    @get_mapping("/{name}")
    async def greet(self, request: Request, name: PathVar[str]):
        return HTMLResponse(f"<h1>{self._svc.greet(name)}</h1>")


class TestControllerStereotypeDiscovery:
    """@controller beans are discovered alongside @rest_controller."""

    @pytest.mark.asyncio
    async def test_collect_routes_discovers_controller(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(GreetingService)
        ctx.register_bean(PageController)
        await ctx.start()

        registrar = ControllerRegistrar()
        routes = registrar.collect_routes(ctx)
        paths = {r.path for r in routes}
        assert "/pages/" in paths
        assert "/pages/{name}" in paths

    @pytest.mark.asyncio
    async def test_collect_route_metadata_discovers_controller(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(GreetingService)
        ctx.register_bean(PageController)
        await ctx.start()

        registrar = ControllerRegistrar()
        metadata = registrar.collect_route_metadata(ctx)
        paths = {m.path for m in metadata}
        assert "/pages/" in paths
        assert "/pages/{name}" in paths

    def test_no_eager_resolution(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(GreetingService)
        ctx.register_bean(PageController)
        # ctx.start() NOT called — beans can't resolve yet

        registrar = ControllerRegistrar()
        routes = registrar.collect_routes(ctx)
        assert len(routes) >= 2


class TestRequestInjection:
    """Handlers that declare `request: Request` get the Starlette Request."""

    def test_inspect_detects_request_param(self):
        async def handler(self, request: Request):
            pass

        resolver = ParameterResolver(handler)
        assert len(resolver.params) == 1
        assert resolver.params[0].name == "request"
        assert resolver.params[0].binding_type is Request

    def test_inspect_request_alongside_path_var(self):
        async def handler(self, request: Request, name: PathVar[str]):
            pass

        resolver = ParameterResolver(handler)
        assert len(resolver.params) == 2
        names = {p.name for p in resolver.params}
        assert "request" in names
        assert "name" in names

    @pytest.mark.asyncio
    async def test_resolve_injects_request_object(self):
        async def handler(self, request: Request):
            pass

        resolver = ParameterResolver(handler)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/pages/",
            "path_params": {},
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)
        kwargs = await resolver.resolve(request)
        assert kwargs["request"] is request

    @pytest.mark.asyncio
    async def test_resolve_request_with_path_var(self):
        async def handler(self, request: Request, name: PathVar[str]):
            pass

        resolver = ParameterResolver(handler)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/pages/alice",
            "path_params": {"name": "alice"},
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)
        kwargs = await resolver.resolve(request)
        assert kwargs["request"] is request
        assert kwargs["name"] == "alice"


class TestControllerIntegrationEndToEnd:
    """End-to-end: @controller + Request injection + HTMLResponse."""

    @pytest.mark.asyncio
    async def test_controller_returns_html(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(GreetingService)
        ctx.register_bean(PageController)
        await ctx.start()

        registrar = ControllerRegistrar()
        routes = registrar.collect_routes(ctx)

        from starlette.applications import Starlette

        app = Starlette(routes=routes)
        client = TestClient(app)

        response = client.get("/pages/")
        assert response.status_code == 200
        assert "Hello, World!" in response.text

    @pytest.mark.asyncio
    async def test_controller_with_path_var_returns_html(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(GreetingService)
        ctx.register_bean(PageController)
        await ctx.start()

        registrar = ControllerRegistrar()
        routes = registrar.collect_routes(ctx)

        from starlette.applications import Starlette

        app = Starlette(routes=routes)
        client = TestClient(app)

        response = client.get("/pages/Alice")
        assert response.status_code == 200
        assert "Hello, Alice!" in response.text
