"""Tests for actuator beans, env, info endpoints and create_app wiring."""

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

from pyfly.actuator.endpoints import make_actuator_routes
from pyfly.actuator.health import HealthAggregator, HealthStatus
from pyfly.container.stereotypes import component, service
from pyfly.context.application_context import ApplicationContext
from pyfly.core.config import Config
from pyfly.web.app import create_app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@component
class DummyComponent:
    pass


@service
class DummyService:
    pass


class SimpleHealthIndicator:
    """A HealthIndicator bean for wiring tests."""

    async def health(self) -> HealthStatus:
        return HealthStatus(status="UP", details={"test": True})


# ---------------------------------------------------------------------------
# /actuator/beans
# ---------------------------------------------------------------------------

class TestBeansEndpoint:
    @pytest.mark.asyncio
    async def test_lists_registered_beans(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(DummyComponent)
        ctx.register_bean(DummyService)
        await ctx.start()

        agg = HealthAggregator()
        routes = make_actuator_routes(health_aggregator=agg, context=ctx)
        app = Starlette(routes=routes)
        client = TestClient(app)

        resp = client.get("/actuator/beans")
        assert resp.status_code == 200
        data = resp.json()
        assert "beans" in data
        # DummyComponent and DummyService should be listed (plus Config itself)
        bean_names = list(data["beans"].keys())
        assert "DummyComponent" in bean_names
        assert "DummyService" in bean_names

    @pytest.mark.asyncio
    async def test_bean_details_include_type_scope_stereotype(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(DummyService)
        await ctx.start()

        agg = HealthAggregator()
        routes = make_actuator_routes(health_aggregator=agg, context=ctx)
        app = Starlette(routes=routes)
        client = TestClient(app)

        resp = client.get("/actuator/beans")
        svc_info = resp.json()["beans"]["DummyService"]
        assert "type" in svc_info
        assert svc_info["scope"] == "SINGLETON"
        assert svc_info["stereotype"] == "service"


# ---------------------------------------------------------------------------
# /actuator/env
# ---------------------------------------------------------------------------

class TestEnvEndpoint:
    @pytest.mark.asyncio
    async def test_shows_active_profiles(self):
        cfg = Config({"pyfly": {"profiles": {"active": "dev,test"}}})
        ctx = ApplicationContext(cfg)
        await ctx.start()

        agg = HealthAggregator()
        routes = make_actuator_routes(health_aggregator=agg, context=ctx)
        app = Starlette(routes=routes)
        client = TestClient(app)

        resp = client.get("/actuator/env")
        assert resp.status_code == 200
        data = resp.json()
        assert "activeProfiles" in data
        assert "dev" in data["activeProfiles"]
        assert "test" in data["activeProfiles"]


# ---------------------------------------------------------------------------
# /actuator/info
# ---------------------------------------------------------------------------

class TestInfoEndpoint:
    @pytest.mark.asyncio
    async def test_returns_app_info(self):
        cfg = Config({"app": {"name": "myapp", "version": "1.0.0", "description": "A test app"}})
        ctx = ApplicationContext(cfg)
        await ctx.start()

        agg = HealthAggregator()
        routes = make_actuator_routes(health_aggregator=agg, context=ctx)
        app = Starlette(routes=routes)
        client = TestClient(app)

        resp = client.get("/actuator/info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["app"]["name"] == "myapp"
        assert data["app"]["version"] == "1.0.0"
        assert data["app"]["description"] == "A test app"


# ---------------------------------------------------------------------------
# create_app(..., actuator_enabled=True)
# ---------------------------------------------------------------------------

class TestCreateAppActuatorWiring:
    @pytest.mark.asyncio
    async def test_actuator_endpoints_present_when_enabled(self):
        ctx = ApplicationContext(Config({}))
        await ctx.start()

        app = create_app(context=ctx, actuator_enabled=True)
        client = TestClient(app)

        # /actuator/health should be present
        resp = client.get("/actuator/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "UP"

        # /actuator/beans should be present (context was provided)
        resp = client.get("/actuator/beans")
        assert resp.status_code == 200
        assert "beans" in resp.json()

        # /actuator/env should be present
        resp = client.get("/actuator/env")
        assert resp.status_code == 200

        # /actuator/info should be present
        resp = client.get("/actuator/info")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_actuator_not_present_when_disabled(self):
        ctx = ApplicationContext(Config({}))
        await ctx.start()

        app = create_app(context=ctx, actuator_enabled=False)
        client = TestClient(app, raise_server_exceptions=False)

        resp = client.get("/actuator/health")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_health_indicators_auto_discovered(self):
        ctx = ApplicationContext(Config({}))
        # Register a HealthIndicator bean manually
        ctx.register_bean(SimpleHealthIndicator)
        ctx.container.bind(SimpleHealthIndicator, SimpleHealthIndicator)
        await ctx.start()

        app = create_app(context=ctx, actuator_enabled=True)
        client = TestClient(app)

        resp = client.get("/actuator/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "UP"
        # The indicator should be auto-discovered
        assert "SimpleHealthIndicator" in data.get("components", {})
