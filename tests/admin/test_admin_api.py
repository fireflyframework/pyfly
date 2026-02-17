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
"""Integration tests for admin REST API."""

import pytest
from starlette.testclient import TestClient
from starlette.applications import Starlette

from pyfly.admin.adapters.starlette import AdminRouteBuilder
from pyfly.admin.config import AdminProperties
from pyfly.admin.providers.beans_provider import BeansProvider
from pyfly.admin.providers.cache_provider import CacheProvider
from pyfly.admin.providers.config_provider import ConfigProvider
from pyfly.admin.providers.cqrs_provider import CqrsProvider
from pyfly.admin.providers.env_provider import EnvProvider
from pyfly.admin.providers.health_provider import HealthProvider
from pyfly.admin.providers.loggers_provider import LoggersProvider
from pyfly.admin.providers.mappings_provider import MappingsProvider
from pyfly.admin.providers.metrics_provider import MetricsProvider
from pyfly.admin.providers.overview_provider import OverviewProvider
from pyfly.admin.providers.scheduled_provider import ScheduledProvider
from pyfly.admin.providers.traces_provider import TracesProvider
from pyfly.admin.registry import AdminViewRegistry
from tests.admin.test_providers import _make_mock_context


@pytest.fixture
def admin_client():
    ctx = _make_mock_context()
    ctx.config._data = {"pyfly": {"app": {"name": "test"}, "web": {"port": 8080}}}
    ctx.config.loaded_sources = []
    props = AdminProperties()

    builder = AdminRouteBuilder(
        properties=props,
        overview=OverviewProvider(ctx, None),
        beans=BeansProvider(ctx),
        health=HealthProvider(None),
        env=EnvProvider(ctx),
        config=ConfigProvider(ctx),
        loggers=LoggersProvider(),
        metrics=MetricsProvider(),
        scheduled=ScheduledProvider(ctx),
        mappings=MappingsProvider(ctx),
        caches=CacheProvider(ctx),
        cqrs=CqrsProvider(ctx),
        traces=TracesProvider(None),
        view_registry=AdminViewRegistry(),
    )
    routes = builder.build_routes()
    app = Starlette(routes=routes)
    return TestClient(app)


class TestAdminAPI:
    def test_overview(self, admin_client):
        resp = admin_client.get("/admin/api/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert "app" in data
        assert "health" in data
        assert "beans" in data

    def test_beans(self, admin_client):
        resp = admin_client.get("/admin/api/beans")
        assert resp.status_code == 200
        data = resp.json()
        assert "beans" in data

    def test_health(self, admin_client):
        resp = admin_client.get("/admin/api/health")
        assert resp.status_code == 200

    def test_loggers(self, admin_client):
        resp = admin_client.get("/admin/api/loggers")
        assert resp.status_code == 200
        data = resp.json()
        assert "ROOT" in data["loggers"]

    def test_settings(self, admin_client):
        resp = admin_client.get("/admin/api/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "PyFly Admin"
