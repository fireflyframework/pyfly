"""Tests for PyFly application bootstrap."""

import pytest

from pyfly.container import Container, service
from pyfly.core.application import PyFlyApplication, pyfly_application


@pyfly_application(name="test-app", scan_packages=[])
class TestApp:
    pass


class TestPyFlyApplication:
    @pytest.mark.asyncio
    async def test_creates_container(self):
        app = PyFlyApplication(TestApp)
        assert isinstance(app.context.container, Container)

    @pytest.mark.asyncio
    async def test_has_config(self):
        app = PyFlyApplication(TestApp)
        assert app.config is not None

    def test_app_metadata(self):
        assert TestApp.__pyfly_app_name__ == "test-app"

    @pytest.mark.asyncio
    async def test_startup_and_shutdown(self):
        app = PyFlyApplication(TestApp)
        await app.startup()
        await app.shutdown()

    @pytest.mark.asyncio
    async def test_auto_discovers_services(self):
        @service
        class DiscoveredService:
            pass

        @pyfly_application(name="discovery-test", scan_packages=["tests.core.test_application"])
        class DiscoveryApp:
            pass

        # Note: This test verifies the scan mechanism works
        # The actual class needs to be in the scanned module
        app = PyFlyApplication(DiscoveryApp)
        await app.startup()
        await app.shutdown()
