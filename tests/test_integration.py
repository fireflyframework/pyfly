"""End-to-end integration test exercising multiple PyFly modules together.

Simulates a mini order-service that uses:
- DI Container for dependency injection
- CQRS for command/query routing
- EDA for event publishing
- Cache for result caching
- Security for authorization
- Validation for input validation
- Observability for metrics
- Web layer for HTTP error handling
"""

from dataclasses import dataclass

import pytest
from pydantic import BaseModel
from starlette.testclient import TestClient

from pyfly.cache import InMemoryCache, cache
from pyfly.cqrs import Command, CommandHandler, Mediator, Query, QueryHandler, command_handler, query_handler
from pyfly.eda import EventEnvelope, InMemoryEventBus
from pyfly.kernel.exceptions import ResourceNotFoundException, ValidationException
from pyfly.observability.metrics import MetricsRegistry, counted
from pyfly.security import SecurityContext, secure
from pyfly.testing import assert_event_published, create_test_container
from pyfly.validation import validate_model
from pyfly.web import create_app

# --- Domain models ---

class CreateOrderRequest(BaseModel):
    product: str
    quantity: int
    customer_id: str


@dataclass(frozen=True)
class CreateOrderCommand(Command):
    product: str
    quantity: int
    customer_id: str


@dataclass(frozen=True)
class GetOrderQuery(Query):
    order_id: str


# --- Handlers ---

@command_handler
class CreateOrderHandler(CommandHandler[CreateOrderCommand]):
    async def handle(self, command: CreateOrderCommand) -> dict:
        return {
            "id": "ord-001",
            "product": command.product,
            "quantity": command.quantity,
            "customer_id": command.customer_id,
            "status": "created",
        }


@query_handler
class GetOrderHandler(QueryHandler[GetOrderQuery]):
    async def handle(self, query: GetOrderQuery) -> dict:
        if query.order_id == "ord-001":
            return {"id": "ord-001", "product": "Widget", "status": "created"}
        raise ResourceNotFoundException(
            f"Order {query.order_id} not found",
            code="ORDER_NOT_FOUND",
        )


# --- Integration test ---

class TestEndToEndOrderService:
    @pytest.mark.asyncio
    async def test_full_order_flow(self):
        """Simulate creating an order through the full stack."""
        # 1. Set up infrastructure
        container = create_test_container()
        event_bus = InMemoryEventBus()
        cache_backend = InMemoryCache()
        metrics = MetricsRegistry()
        mediator = Mediator()
        published_events: list[EventEnvelope] = []

        async def capture_events(event: EventEnvelope) -> None:
            published_events.append(event)

        event_bus.subscribe("order.*", capture_events)

        # 2. Register handlers
        mediator.register_handler(CreateOrderCommand, CreateOrderHandler())
        mediator.register_handler(GetOrderQuery, GetOrderHandler())

        # 3. Validate input
        request_data = {"product": "Widget", "quantity": 5, "customer_id": "cust-001"}
        validated = validate_model(CreateOrderRequest, request_data)

        # 4. Security check
        ctx = SecurityContext(user_id="user-1", roles=["USER"], permissions=["order:create"])
        assert ctx.is_authenticated
        assert ctx.has_permission("order:create")

        # 5. Send command through CQRS mediator
        command = CreateOrderCommand(
            product=validated.product,
            quantity=validated.quantity,
            customer_id=validated.customer_id,
        )
        order = await mediator.send(command)
        assert order["id"] == "ord-001"
        assert order["status"] == "created"

        # 6. Publish event
        await event_bus.publish("order-events", "order.created", order)
        assert_event_published(published_events, "order.created", payload_contains={"id": "ord-001"})

        # 7. Query with caching
        @cache(backend=cache_backend, key="order:{order_id}")
        async def get_cached_order(order_id: str) -> dict:
            return await mediator.send(GetOrderQuery(order_id=order_id))

        result1 = await get_cached_order("ord-001")
        result2 = await get_cached_order("ord-001")  # From cache
        assert result1 == result2
        assert result1["product"] == "Widget"

        # 8. Metrics
        @counted(metrics, "orders_created_total", "Total orders created")
        async def tracked_create(data: dict) -> dict:
            return data

        await tracked_create(order)
        counter = metrics._counters["orders_created_total"]
        assert counter._value.get() == 1.0

    @pytest.mark.asyncio
    async def test_validation_rejects_bad_input(self):
        """Validate that bad input is caught before reaching the handler."""
        with pytest.raises(ValidationException) as exc_info:
            validate_model(CreateOrderRequest, {"product": "Widget"})
        assert exc_info.value.code == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_security_blocks_unauthorized(self):
        """Verify that the @secure decorator blocks unauthorized access."""
        @secure(roles=["ADMIN"])
        async def admin_endpoint(security_context: SecurityContext) -> str:
            return "admin data"

        user_ctx = SecurityContext(user_id="user-1", roles=["USER"])
        with pytest.raises(Exception, match="Insufficient roles"):
            await admin_endpoint(security_context=user_ctx)

    @pytest.mark.asyncio
    async def test_not_found_propagates(self):
        """Verify ResourceNotFoundException propagates from query handler."""
        mediator = Mediator()
        mediator.register_handler(GetOrderQuery, GetOrderHandler())

        with pytest.raises(ResourceNotFoundException, match="not found"):
            await mediator.send(GetOrderQuery(order_id="nonexistent"))

    def test_web_error_handling(self):
        """Verify that framework exceptions are properly mapped to HTTP responses."""
        app = create_app(title="test")

        @app.route("/order/{order_id}")
        async def get_order(request):
            raise ResourceNotFoundException("Order not found", code="ORDER_NOT_FOUND")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/order/123")
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"]["code"] == "ORDER_NOT_FOUND"


class TestOpenAPIIntegration:
    def test_openapi_with_router_and_error_handling(self):
        """Verify OpenAPI docs work alongside error handling and routers."""
        from pyfly.web.router import PyFlyRouter

        router = PyFlyRouter(prefix="/api/orders", tags=["Orders"])

        @router.get("/{order_id}", summary="Get order by ID")
        async def get_order(request):
            from starlette.responses import JSONResponse
            order_id = request.path_params["order_id"]
            if order_id == "missing":
                raise ResourceNotFoundException("Order not found", code="ORDER_NOT_FOUND")
            return JSONResponse({"id": order_id, "status": "created"})

        @router.post("/", status_code=201, summary="Create order")
        async def create_order(request):
            from starlette.responses import JSONResponse
            return JSONResponse({"id": "ord-001", "status": "created"}, status_code=201)

        app = create_app(title="Order Service", version="1.0.0", routers=[router])
        client = TestClient(app, raise_server_exceptions=False)

        # OpenAPI spec is served
        spec_resp = client.get("/openapi.json")
        assert spec_resp.status_code == 200
        spec = spec_resp.json()
        assert "/api/orders/{order_id}" in spec["paths"]
        assert "/api/orders/" in spec["paths"]

        # Swagger UI and ReDoc are served
        assert client.get("/docs").status_code == 200
        assert client.get("/redoc").status_code == 200

        # Routes actually work
        resp = client.get("/api/orders/ord-001")
        assert resp.status_code == 200
        assert resp.json()["id"] == "ord-001"

        # Error handling still works
        resp = client.get("/api/orders/missing")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "ORDER_NOT_FOUND"
