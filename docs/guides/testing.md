# Testing Guide

This guide covers the testing utilities that PyFly provides out of the box: a base
test case class, a test container factory, and event assertion helpers. Together,
these tools make it straightforward to write unit tests, integration tests, and
event-driven tests for PyFly applications.

---

## Table of Contents

1. [Introduction](#introduction)
   - [Testing Pyramid](#testing-pyramid)
2. [PyFlyTestCase](#pyflytestcase)
   - [Setup and Teardown](#setup-and-teardown)
   - [Available Fixtures](#available-fixtures)
3. [create_test_container()](#create_test_container)
   - [Basic Usage](#basic-usage)
   - [Injecting Mocks and Fakes](#injecting-mocks-and-fakes)
   - [Resolving Services in Tests](#resolving-services-in-tests)
4. [Event Assertions](#event-assertions)
   - [assert_event_published()](#assert_event_published)
   - [assert_no_events_published()](#assert_no_events_published)
5. [Testing Patterns](#testing-patterns)
   - [Unit Testing Services](#unit-testing-services)
   - [Integration Testing with In-Memory Adapters](#integration-testing-with-in-memory-adapters)
   - [Testing Controllers](#testing-controllers)
   - [Testing Event Handlers](#testing-event-handlers)
6. [Complete Example](#complete-example)

---

## Introduction

PyFly adopts a "testing is a first-class citizen" philosophy. The framework provides
dedicated testing modules so you never have to build boilerplate setup from scratch.

```python
from pyfly.testing import (
    PyFlyTestCase,
    create_test_container,
    assert_event_published,
    assert_no_events_published,
)
```

**Source:** `src/pyfly/testing/__init__.py`

### Testing Pyramid

PyFly encourages the standard testing pyramid, where the number of tests decreases
as the scope and cost of each test increases:

```
          /\
         /  \       End-to-end tests (few)
        /    \      - Full application stack with HTTP client
       /------\
      /        \    Integration tests (some)
     /          \   - Real components, in-memory adapters
    /------------\
   /              \ Unit tests (many)
  /                \ - Mocked dependencies, fast execution
 /------------------\
```

| Level       | Dependencies          | Speed  | PyFly Tools                              |
|-------------|-----------------------|--------|------------------------------------------|
| Unit        | Mocked                | Fast   | `create_test_container()`, `unittest.mock` |
| Integration | In-memory adapters    | Medium | `PyFlyTestCase`, `InMemoryEventBus`      |
| E2E         | Full stack            | Slow   | `create_app()` + `httpx.AsyncClient`     |

---

## PyFlyTestCase

`PyFlyTestCase` is a base class for integration tests that need PyFly framework
infrastructure. It pre-configures an `ApplicationContext` and an `InMemoryEventBus`
so your tests can focus on behavior rather than setup.

```python
from pyfly.testing import PyFlyTestCase


class TestOrderWorkflow(PyFlyTestCase):

    async def test_full_order_lifecycle(self):
        await self.setup()

        # self.context is a fully initialized ApplicationContext
        # self.event_bus is an InMemoryEventBus ready for subscriptions

        # ... test logic ...

        await self.teardown()
```

### Setup and Teardown

Both methods are `async` and must be awaited. Call `setup()` at the beginning of
each test and `teardown()` at the end to ensure clean state between tests.

| Method       | What It Does                                                    |
|-------------|------------------------------------------------------------------|
| `setup()`   | 1. Creates an `ApplicationContext` with an empty `Config({})`.   |
|             | 2. Creates a fresh `InMemoryEventBus` instance.                  |
|             | 3. Calls `await context.start()` to initialize the context.     |
| `teardown()` | 1. Calls `await context.stop()` to clean up resources.         |

The internal implementation:

```python
class PyFlyTestCase:
    context: ApplicationContext
    event_bus: InMemoryEventBus

    async def setup(self) -> None:
        self.context = ApplicationContext(Config({}))
        self.event_bus = InMemoryEventBus()
        await self.context.start()

    async def teardown(self) -> None:
        await self.context.stop()
```

### Available Fixtures

After calling `setup()`, the following attributes are available:

| Attribute      | Type                  | Description                              |
|---------------|-----------------------|------------------------------------------|
| `self.context`  | `ApplicationContext` | Pre-configured application context with empty config |
| `self.event_bus` | `InMemoryEventBus` | In-memory event bus for publishing and subscribing |

The `InMemoryEventBus` supports wildcard pattern subscriptions (e.g., `"order.*"`
matches `"order.created"` and `"order.shipped"`), making it easy to capture events
in tests.

**Source:** `src/pyfly/testing/fixtures.py`

---

## create_test_container()

`create_test_container()` creates a pre-configured DI `Container` for testing. It
accepts an optional `overrides` dictionary that maps interface types to test
implementations, enabling you to substitute real services with fakes or mocks.

### Basic Usage

```python
from pyfly.testing import create_test_container

# Create a container with no overrides
container = create_test_container()
```

### Injecting Mocks and Fakes

The `overrides` parameter maps interface types to test implementations. Each override
is registered as a `SINGLETON` and bound to the interface.

```python
from pyfly.testing import create_test_container


class FakeOrderRepository:
    """In-memory order repository for testing."""

    def __init__(self):
        self.orders: dict[str, dict] = {}

    async def save(self, order: dict) -> None:
        self.orders[order["id"]] = order

    async def find_by_id(self, order_id: str) -> dict | None:
        return self.orders.get(order_id)


# Create container with the fake repository
container = create_test_container(overrides={
    OrderRepository: FakeOrderRepository,
})
```

**`create_test_container()` Parameters:**

| Parameter   | Type                       | Default | Description                                |
|------------|----------------------------|---------|--------------------------------------------|
| `overrides` | `dict[type, type] \| None` | `None`  | Interface-to-implementation mappings       |

**How overrides work internally:**

For each `(interface, impl)` pair in the overrides dictionary:

1. The implementation is registered with `container.register(impl, scope=Scope.SINGLETON)`.
2. If `interface != impl`, a binding is created with `container.bind(interface, impl)`.

This means you can `resolve()` by the interface type and receive the test implementation:

```python
repo = container.resolve(OrderRepository)
# Returns a FakeOrderRepository instance (singleton)
```

The full implementation:

```python
def create_test_container(
    overrides: dict[type, type] | None = None,
) -> Container:
    container = Container()
    if overrides:
        for interface, impl in overrides.items():
            container.register(impl, scope=Scope.SINGLETON)
            if interface != impl:
                container.bind(interface, impl)
    return container
```

**Source:** `src/pyfly/testing/containers.py`

### Resolving Services in Tests

Once the container is configured with overrides, register your service classes and
use `resolve()` to get instances with their dependencies injected:

```python
from pyfly.testing import create_test_container
from pyfly.container import Scope

container = create_test_container(overrides={
    OrderRepository: FakeOrderRepository,
})

# Also register the service that depends on the repository
container.register(OrderService, scope=Scope.SINGLETON)

# Resolve -- OrderService gets FakeOrderRepository injected via constructor
service = container.resolve(OrderService)

# The resolved service uses the fake repository
result = await service.create_order({"id": "ord-1", "customer": "Alice"})
```

---

## Event Assertions

PyFly provides two assertion helpers for verifying event-driven behavior. They work
with lists of `EventEnvelope` objects, which is the standard event wrapper in PyFly's
EDA module.

An `EventEnvelope` contains:

| Field        | Type              | Description                    |
|-------------|-------------------|--------------------------------|
| `event_type` | `str`            | Event type identifier          |
| `payload`    | `dict[str, Any]` | Event data                     |
| `destination` | `str`           | Target destination/topic       |
| `event_id`   | `str`            | Auto-generated UUID            |
| `timestamp`  | `datetime`       | Auto-generated UTC timestamp   |
| `headers`    | `dict[str, str]` | Optional metadata headers      |

### assert_event_published()

Asserts that an event of a given type was published. Optionally verifies that the
event payload contains specific key-value pairs.

```python
from pyfly.testing import assert_event_published
from pyfly.eda.types import EventEnvelope

events = [
    EventEnvelope(
        event_type="order.created",
        payload={"order_id": "ord-123", "customer_id": "cust-42", "total": 99.99},
        destination="orders",
    ),
]

# Assert just the event type
event = assert_event_published(events, "order.created")

# Assert event type AND payload contents
event = assert_event_published(
    events,
    "order.created",
    payload_contains={"order_id": "ord-123", "customer_id": "cust-42"},
)
```

**Parameters:**

| Parameter          | Type                     | Default | Description                            |
|-------------------|--------------------------|---------|----------------------------------------|
| `events`          | `list[EventEnvelope]`    | required | List of captured event envelopes      |
| `event_type`      | `str`                    | required | Expected event type string            |
| `payload_contains` | `dict[str, Any] \| None` | `None`  | Key-value pairs the payload must contain |

**Returns:** The matching `EventEnvelope` instance.

**Raises `AssertionError` when:**

- No event with the given type is found. The error message lists all published event
  types for debugging:
  ```
  Expected event 'order.created' to be published. Published events: ['user.updated']
  ```
- A matching event is found but its payload is missing an expected key:
  ```
  Expected key 'order_id' in event payload
  ```
- A matching event is found but a payload value does not match:
  ```
  Expected payload['order_id'] == 'ord-123', got 'ord-999'
  ```

**How matching works internally:**

1. Filters `events` for those where `event.event_type == event_type`.
2. Takes the **first** match (if there are multiple events of the same type).
3. If `payload_contains` is provided, iterates over each key-value pair and asserts
   presence and equality against `event.payload`.

### assert_no_events_published()

Asserts that no events were published at all. Use this to verify that a failed
operation did not produce side effects.

```python
from pyfly.testing import assert_no_events_published

events: list[EventEnvelope] = []

# Passes -- no events in the list
assert_no_events_published(events)
```

If events are present, the assertion fails with a descriptive message:

```python
events.append(EventEnvelope(
    event_type="order.created",
    payload={"order_id": "ord-123"},
    destination="orders",
))
assert_no_events_published(events)
# AssertionError: Expected no events to be published. Got: ['order.created']
```

**Parameters:**

| Parameter | Type                  | Description                          |
|----------|-----------------------|--------------------------------------|
| `events` | `list[EventEnvelope]` | List of captured event envelopes     |

**Source:** `src/pyfly/testing/assertions.py`

---

## Testing Patterns

### Unit Testing Services

Unit tests mock all external dependencies and test a single class in isolation.
Use `unittest.mock.AsyncMock` for async dependencies.

```python
import pytest
from unittest.mock import AsyncMock
from pyfly.kernel.exceptions import ResourceNotFoundException


class TestOrderService:
    """Pure unit tests -- all dependencies are mocked."""

    @pytest.fixture
    def mock_repo(self):
        repo = AsyncMock()
        repo.find_by_id = AsyncMock(return_value=None)
        repo.save = AsyncMock()
        return repo

    @pytest.fixture
    def service(self, mock_repo):
        return OrderService(order_repository=mock_repo)

    async def test_create_order_saves_to_repository(self, service, mock_repo):
        result = await service.create_order({
            "customer_id": "cust-42",
            "items": [{"product": "Widget", "qty": 1}],
        })

        mock_repo.save.assert_called_once()
        assert result["status"] == "created"

    async def test_create_order_returns_order_id(self, service):
        result = await service.create_order({
            "customer_id": "cust-42",
            "items": [{"product": "Widget", "qty": 1}],
        })
        assert "order_id" in result

    async def test_get_order_raises_not_found(self, service, mock_repo):
        mock_repo.find_by_id.return_value = None

        with pytest.raises(ResourceNotFoundException):
            await service.get_order("nonexistent-id")
```

### Integration Testing with In-Memory Adapters

Integration tests use PyFly's in-memory adapters (such as `InMemoryEventBus`) and
fake repositories to test multiple components working together.

```python
import pytest
from pyfly.testing import PyFlyTestCase, assert_event_published
from pyfly.eda.types import EventEnvelope


class TestOrderEventIntegration(PyFlyTestCase):
    """Tests that verify event publishing and subscription."""

    async def test_order_created_event_is_published_and_received(self):
        await self.setup()

        # Set up an event capture list
        captured_events: list[EventEnvelope] = []

        async def capture(envelope: EventEnvelope) -> None:
            captured_events.append(envelope)

        # Subscribe to order events using wildcard pattern
        self.event_bus.subscribe("order.*", capture)

        # Publish an event (simulating what the service would do)
        await self.event_bus.publish(
            destination="orders",
            event_type="order.created",
            payload={"order_id": "ord-123", "total": 59.99},
        )

        # Verify the event was published correctly
        event = assert_event_published(
            captured_events,
            "order.created",
            payload_contains={"order_id": "ord-123"},
        )
        assert event.payload["total"] == 59.99

        await self.teardown()

    async def test_wildcard_pattern_receives_multiple_event_types(self):
        await self.setup()

        captured: list[EventEnvelope] = []

        async def capture(envelope: EventEnvelope) -> None:
            captured.append(envelope)

        self.event_bus.subscribe("order.*", capture)

        await self.event_bus.publish("orders", "order.created", {"id": "1"})
        await self.event_bus.publish("orders", "order.shipped", {"id": "1"})
        await self.event_bus.publish("users", "user.created", {"id": "u1"})

        # Only order.* events should be captured
        assert len(captured) == 2
        assert_event_published(captured, "order.created")
        assert_event_published(captured, "order.shipped")

        await self.teardown()
```

### Testing Controllers

Test controllers by creating a Starlette test client with `create_app()` and
`httpx.AsyncClient`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from pyfly.web.adapters.starlette import create_app
from pyfly.testing import create_test_container
from pyfly.container import Scope


class TestOrderController:
    """HTTP-level tests for the order controller."""

    @pytest.fixture
    async def client(self):
        # Set up the DI container with test overrides
        container = create_test_container(overrides={
            OrderRepository: FakeOrderRepository,
        })
        container.register(OrderService, scope=Scope.SINGLETON)
        container.register(OrderController, scope=Scope.SINGLETON)

        app = create_app(title="Test", version="0.0.1")
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c

    async def test_create_order_returns_201(self, client):
        response = await client.post("/api/orders", json={
            "customer_id": "cust-42",
            "items": [{"product_id": "SKU-001", "quantity": 2}],
        })
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "created"

    async def test_create_order_invalid_body_returns_422(self, client):
        response = await client.post("/api/orders", json={})
        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "VALIDATION_ERROR"

    async def test_get_order_not_found_returns_404(self, client):
        response = await client.get("/api/orders/nonexistent")
        assert response.status_code == 404
```

### Testing Event Handlers

Test event handlers by directly invoking them with constructed `EventEnvelope`
objects:

```python
import pytest
from unittest.mock import AsyncMock
from pyfly.eda.types import EventEnvelope


class TestOrderCreatedHandler:
    """Tests for the order.created event handler."""

    @pytest.fixture
    def notification_service(self):
        return AsyncMock()

    @pytest.fixture
    def handler(self, notification_service):
        return OrderCreatedHandler(
            notification_service=notification_service,
        )

    async def test_sends_confirmation_notification(self, handler, notification_service):
        envelope = EventEnvelope(
            event_type="order.created",
            payload={"order_id": "ord-123", "customer_id": "cust-42"},
            destination="orders",
        )

        await handler.handle(envelope)

        notification_service.send_confirmation.assert_called_once_with(
            customer_id="cust-42",
            order_id="ord-123",
        )

    async def test_handles_missing_customer_id_gracefully(self, handler):
        envelope = EventEnvelope(
            event_type="order.created",
            payload={"order_id": "ord-123"},  # no customer_id
            destination="orders",
        )

        # Should not raise -- handler should handle missing data gracefully
        await handler.handle(envelope)
```

---

## Complete Example

The following example puts everything together: a service under test with a fake
repository, DI container setup, and event assertions.

```python
"""tests/test_order_service.py"""

import pytest
from unittest.mock import AsyncMock

from pyfly.testing import (
    PyFlyTestCase,
    create_test_container,
    assert_event_published,
    assert_no_events_published,
)
from pyfly.container import Scope
from pyfly.eda.types import EventEnvelope
from pyfly.kernel.exceptions import ResourceNotFoundException, ValidationException


# =========================================================================
# Test Doubles
# =========================================================================

class OrderRepository:
    """Interface for the order repository (used for type binding)."""
    pass


class FakeOrderRepository:
    """In-memory order repository for testing."""

    def __init__(self):
        self.orders: dict[str, dict] = {}

    async def save(self, order: dict) -> None:
        self.orders[order["id"]] = order

    async def find_by_id(self, order_id: str) -> dict | None:
        return self.orders.get(order_id)

    async def find_all(self) -> list[dict]:
        return list(self.orders.values())


# =========================================================================
# Service Under Test
# =========================================================================

class OrderService:
    def __init__(self, order_repository: OrderRepository) -> None:
        self._repo = order_repository

    async def create_order(self, data: dict) -> dict:
        if "customer_id" not in data:
            raise ValidationException("customer_id is required")
        order = {
            "id": "ord-001",
            "customer_id": data["customer_id"],
            "status": "created",
        }
        await self._repo.save(order)
        return order

    async def get_order(self, order_id: str) -> dict:
        order = await self._repo.find_by_id(order_id)
        if order is None:
            raise ResourceNotFoundException(
                f"Order {order_id} not found",
                code="ORDER_NOT_FOUND",
            )
        return order


# =========================================================================
# Unit Tests -- fast, isolated, mocked dependencies
# =========================================================================

class TestOrderServiceUnit:

    @pytest.fixture
    def mock_repo(self):
        return AsyncMock(spec=FakeOrderRepository)

    @pytest.fixture
    def service(self, mock_repo):
        return OrderService(order_repository=mock_repo)

    async def test_create_order_success(self, service, mock_repo):
        result = await service.create_order({"customer_id": "cust-42"})

        assert result["status"] == "created"
        assert result["customer_id"] == "cust-42"
        mock_repo.save.assert_called_once()

    async def test_create_order_missing_customer_raises(self, service):
        with pytest.raises(ValidationException, match="customer_id is required"):
            await service.create_order({})

    async def test_get_order_not_found_raises(self, service, mock_repo):
        mock_repo.find_by_id.return_value = None

        with pytest.raises(ResourceNotFoundException):
            await service.get_order("nonexistent")


# =========================================================================
# Integration Tests -- real components, in-memory adapters
# =========================================================================

class TestOrderServiceIntegration:

    @pytest.fixture
    def container(self):
        container = create_test_container(overrides={
            OrderRepository: FakeOrderRepository,
        })
        container.register(OrderService, scope=Scope.SINGLETON)
        return container

    @pytest.fixture
    def service(self, container) -> OrderService:
        return container.resolve(OrderService)

    @pytest.fixture
    def repo(self, container) -> FakeOrderRepository:
        return container.resolve(OrderRepository)

    async def test_create_and_retrieve_order(self, service, repo):
        # Create an order
        created = await service.create_order({"customer_id": "cust-42"})
        assert created["status"] == "created"

        # Retrieve it from the repository
        fetched = await service.get_order(created["id"])
        assert fetched["customer_id"] == "cust-42"

        # Verify it was persisted in the fake repository
        assert created["id"] in repo.orders

    async def test_repository_is_shared_singleton(self, container):
        repo1 = container.resolve(OrderRepository)
        repo2 = container.resolve(OrderRepository)
        assert repo1 is repo2  # Same singleton instance


# =========================================================================
# Event Tests -- verify event publishing behavior
# =========================================================================

class TestOrderEvents(PyFlyTestCase):

    async def test_order_created_event(self):
        await self.setup()

        captured: list[EventEnvelope] = []

        async def capture(envelope: EventEnvelope) -> None:
            captured.append(envelope)

        self.event_bus.subscribe("order.*", capture)

        # Simulate publishing an order created event
        await self.event_bus.publish(
            destination="orders",
            event_type="order.created",
            payload={
                "order_id": "ord-001",
                "customer_id": "cust-42",
                "total": 149.97,
            },
        )

        # Assert the event with payload matching
        event = assert_event_published(
            captured,
            "order.created",
            payload_contains={
                "order_id": "ord-001",
                "customer_id": "cust-42",
            },
        )
        assert event.payload["total"] == 149.97
        assert event.destination == "orders"

        await self.teardown()

    async def test_no_events_when_validation_fails(self):
        await self.setup()

        captured: list[EventEnvelope] = []

        async def capture(envelope: EventEnvelope) -> None:
            captured.append(envelope)

        self.event_bus.subscribe("order.*", capture)

        # Validation failure should not produce events
        # (no publish call was made)
        assert_no_events_published(captured)

        await self.teardown()
```

Run the tests:

```bash
# Run all tests with verbose output
pytest tests/test_order_service.py -v

# Run only unit tests
pytest tests/test_order_service.py::TestOrderServiceUnit -v

# Run only integration tests
pytest tests/test_order_service.py::TestOrderServiceIntegration -v

# Run with async support (if using pytest-asyncio)
pytest tests/test_order_service.py -v --asyncio-mode=auto
```
