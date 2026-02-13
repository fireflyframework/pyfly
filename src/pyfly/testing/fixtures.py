"""Base test case and fixtures for PyFly applications."""

from __future__ import annotations

from pyfly.container import Container
from pyfly.eda import InMemoryEventBus


class PyFlyTestCase:
    """Base test case providing pre-configured container and event bus.

    Subclass this for integration tests that need framework infrastructure:

        class TestOrderService(PyFlyTestCase):
            async def test_create_order(self):
                await self.setup()
                # ... use self.container and self.event_bus
                await self.teardown()
    """

    container: Container
    event_bus: InMemoryEventBus

    async def setup(self) -> None:
        """Initialize test infrastructure."""
        self.container = Container()
        self.event_bus = InMemoryEventBus()
        await self.container.startup()

    async def teardown(self) -> None:
        """Clean up test infrastructure."""
        await self.container.shutdown()
