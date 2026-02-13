"""Base test case and fixtures for PyFly applications."""

from __future__ import annotations

from pyfly.context.application_context import ApplicationContext
from pyfly.core.config import Config
from pyfly.eda import InMemoryEventBus


class PyFlyTestCase:
    """Base test case providing pre-configured ApplicationContext and event bus.

    Subclass this for integration tests that need framework infrastructure:

        class TestOrderService(PyFlyTestCase):
            async def test_create_order(self):
                await self.setup()
                # ... use self.context and self.event_bus
                await self.teardown()
    """

    context: ApplicationContext
    event_bus: InMemoryEventBus

    async def setup(self) -> None:
        """Initialize test infrastructure."""
        self.context = ApplicationContext(Config({}))
        self.event_bus = InMemoryEventBus()
        await self.context.start()

    async def teardown(self) -> None:
        """Clean up test infrastructure."""
        await self.context.stop()
