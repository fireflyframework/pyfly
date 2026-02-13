"""Tests for async lifecycle hooks."""

import pytest

from pyfly.container import Container, Scope, injectable


@injectable
class ServiceWithLifecycle:
    def __init__(self) -> None:
        self.initialized = False
        self.destroyed = False

    async def on_init(self) -> None:
        self.initialized = True

    async def on_destroy(self) -> None:
        self.destroyed = True


class TestLifecycleHooks:
    @pytest.mark.asyncio
    async def test_on_init_called_after_startup(self):
        container = Container()
        container.register(ServiceWithLifecycle)
        service = container.resolve(ServiceWithLifecycle)
        assert not service.initialized
        await container.startup()
        assert service.initialized

    @pytest.mark.asyncio
    async def test_on_destroy_called_on_shutdown(self):
        container = Container()
        container.register(ServiceWithLifecycle)
        service = container.resolve(ServiceWithLifecycle)
        await container.startup()
        assert not service.destroyed
        await container.shutdown()
        assert service.destroyed

    @pytest.mark.asyncio
    async def test_services_without_hooks_are_fine(self):
        @injectable
        class PlainService:
            pass

        container = Container()
        container.register(PlainService)
        container.resolve(PlainService)
        # Should not raise
        await container.startup()
        await container.shutdown()
