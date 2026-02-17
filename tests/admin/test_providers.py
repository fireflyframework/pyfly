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
"""Tests for admin data providers."""

from unittest.mock import AsyncMock, MagicMock

from pyfly.admin.providers.beans_provider import BeansProvider
from pyfly.admin.providers.health_provider import HealthProvider
from pyfly.admin.providers.overview_provider import OverviewProvider
from pyfly.container.types import Scope


def _make_mock_context():
    """Create a mock ApplicationContext with sample beans."""
    ctx = MagicMock()
    ctx.config = MagicMock()
    ctx.config.get = MagicMock(side_effect=lambda key, default=None: {
        "pyfly.app.name": "test-app",
        "pyfly.app.version": "1.0.0",
        "pyfly.app.description": "Test Application",
    }.get(key, default))
    ctx.environment = MagicMock()
    ctx.environment.active_profiles = ["dev"]
    ctx.bean_count = 5
    ctx.wiring_counts = {"event_listeners": 2, "scheduled": 1}
    ctx.get_bean_counts_by_stereotype.return_value = {
        "service": 3, "repository": 2, "rest_controller": 1
    }

    # Mock container registrations
    class FakeService:
        __pyfly_stereotype__ = "service"
    class FakeRepo:
        __pyfly_stereotype__ = "repository"

    reg1 = MagicMock()
    reg1.name = "fakeService"
    reg1.scope = Scope.SINGLETON
    reg1.instance = FakeService()
    reg1.condition = None

    reg2 = MagicMock()
    reg2.name = "fakeRepo"
    reg2.scope = Scope.SINGLETON
    reg2.instance = FakeRepo()
    reg2.condition = None

    ctx.container._registrations = {FakeService: reg1, FakeRepo: reg2}
    return ctx


class TestBeansProvider:
    async def test_get_beans(self):
        ctx = _make_mock_context()
        provider = BeansProvider(ctx)
        result = await provider.get_beans()
        assert "beans" in result
        assert len(result["beans"]) == 2
        bean = result["beans"][0]
        assert "name" in bean
        assert "type" in bean
        assert "scope" in bean
        assert "stereotype" in bean


class TestHealthProvider:
    async def test_get_health(self):
        aggregator = MagicMock()
        aggregator.check = AsyncMock(return_value=MagicMock(
            status="UP",
            to_dict=MagicMock(return_value={
                "status": "UP",
                "components": {"db": {"status": "UP", "details": {}}}
            })
        ))
        provider = HealthProvider(aggregator)
        result = await provider.get_health()
        assert result["status"] == "UP"


class TestOverviewProvider:
    async def test_get_overview(self):
        ctx = _make_mock_context()
        aggregator = MagicMock()
        aggregator.check = AsyncMock(return_value=MagicMock(
            status="UP",
            to_dict=MagicMock(return_value={"status": "UP", "components": {}})
        ))
        provider = OverviewProvider(ctx, aggregator)
        result = await provider.get_overview()
        assert result["app"]["name"] == "test-app"
        assert result["health"]["status"] == "UP"
        assert result["beans"]["total"] == 5
        assert "stereotypes" in result["beans"]
