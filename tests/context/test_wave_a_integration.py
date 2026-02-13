"""Wave A integration test: stereotypes + ApplicationContext + lifecycle + events."""

import pytest

from pyfly.container.bean import bean, primary
from pyfly.container.stereotypes import (
    component,
    configuration,
    repository,
    rest_controller,
    service,
)
from pyfly.container.types import Scope
from pyfly.context.application_context import ApplicationContext
from pyfly.context.events import ApplicationReadyEvent, ContextRefreshedEvent, app_event_listener
from pyfly.context.lifecycle import post_construct, pre_destroy
from pyfly.core.config import Config


# --- Domain layer ---

class OrderRepository:
    """Interface."""
    async def find(self, order_id: str) -> dict | None: ...
    async def save(self, data: dict) -> dict: ...


@repository
@primary
class InMemoryOrderRepository:
    def __init__(self):
        self._store: dict[str, dict] = {}

    @post_construct
    async def seed(self):
        self._store["ord-001"] = {"id": "ord-001", "product": "Widget", "status": "created"}

    async def find(self, order_id: str) -> dict | None:
        return self._store.get(order_id)

    async def save(self, data: dict) -> dict:
        self._store[data["id"]] = data
        return data


@service
class OrderService:
    def __init__(self, repo: InMemoryOrderRepository):
        self._repo = repo

    async def get_order(self, order_id: str) -> dict | None:
        return await self._repo.find(order_id)


@configuration
class AppConfig:
    @bean(name="appName")
    def app_name(self) -> str:
        return "Order Service"


@service(name="auditService")
class AuditService:
    def __init__(self):
        self.events: list[str] = []

    @app_event_listener
    async def on_ready(self, event: ApplicationReadyEvent) -> None:
        self.events.append("ready")


# --- Integration test ---

class TestWaveAIntegration:
    @pytest.mark.asyncio
    async def test_full_spring_like_flow(self):
        """Simulate a Spring Boot-like application lifecycle."""
        # 1. Create context
        ctx = ApplicationContext(Config({}))

        # 2. Register beans (normally done by scanner)
        ctx.register_bean(InMemoryOrderRepository)
        ctx.register_bean(OrderService)
        ctx.register_bean(AppConfig)
        ctx.register_bean(AuditService)

        # Wire up event listener manually for this test
        # (In real app, context would auto-discover @app_event_listener)
        audit = None

        async def capture_ready(event):
            nonlocal audit
            if audit:
                await audit.on_ready(event)

        ctx.event_bus.subscribe(ApplicationReadyEvent, capture_ready)

        # 3. Start context
        await ctx.start()

        # 4. Verify beans resolved
        order_svc = ctx.get_bean(OrderService)
        assert order_svc is not None

        # 5. Verify @post_construct ran (seed data)
        order = await order_svc.get_order("ord-001")
        assert order is not None
        assert order["product"] == "Widget"

        # 6. Verify @bean factory ran
        app_name = ctx.get_bean_by_name("appName")
        assert app_name == "Order Service"

        # 7. Verify named bean
        audit = ctx.get_bean_by_name("auditService")
        assert isinstance(audit, AuditService)

        # 8. Shutdown
        await ctx.stop()
