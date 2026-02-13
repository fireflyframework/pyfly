"""Tests for PyFlyApplication integration with ApplicationContext."""

import pytest

from pyfly.container.stereotypes import service
from pyfly.context.application_context import ApplicationContext
from pyfly.core.application import PyFlyApplication, pyfly_application


class TestPyFlyApplicationContext:
    @pytest.mark.asyncio
    async def test_application_has_context(self):
        @pyfly_application(name="test-app")
        class TestApp:
            pass

        app = PyFlyApplication(TestApp)
        assert isinstance(app.context, ApplicationContext)

    @pytest.mark.asyncio
    async def test_startup_starts_context(self):
        @pyfly_application(name="test-app")
        class TestApp:
            pass

        app = PyFlyApplication(TestApp)
        await app.startup()
        assert app.context._started is True
        await app.shutdown()

    @pytest.mark.asyncio
    async def test_container_still_accessible(self):
        @pyfly_application(name="test-app")
        class TestApp:
            pass

        app = PyFlyApplication(TestApp)
        # Backward compatibility: .container still works
        assert app.container is app.context.container
