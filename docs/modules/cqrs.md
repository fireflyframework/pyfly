# CQRS Guide

Command/Query Responsibility Segregation (CQRS) is an architectural pattern
that separates read operations (queries) from write operations (commands).
PyFly's `pyfly.cqrs` module provides the building blocks -- `Command`, `Query`,
typed handlers, a `Mediator` for dispatch, and a pluggable middleware pipeline
for cross-cutting concerns.

---

## Table of Contents

1. [Why CQRS?](#why-cqrs)
2. [Core Concepts](#core-concepts)
3. [Commands](#commands)
4. [Queries](#queries)
5. [CommandHandler](#commandhandler)
6. [QueryHandler](#queryhandler)
7. [Handler Decorators: @command_handler and @query_handler](#handler-decorators-command_handler-and-query_handler)
8. [The Mediator](#the-mediator)
   - [Registering Handlers](#registering-handlers)
   - [Dispatching Messages](#dispatching-messages)
   - [Error Handling](#error-handling)
9. [Middleware Pipeline](#middleware-pipeline)
   - [CqrsMiddleware Protocol](#cqrsmiddleware-protocol)
   - [LoggingMiddleware](#loggingmiddleware)
   - [MetricsMiddleware](#metricsmiddleware)
   - [Writing Custom Middleware](#writing-custom-middleware)
   - [Middleware Execution Order](#middleware-execution-order)
10. [Complete Example: Order Management](#complete-example-order-management)
11. [Testing CQRS Components](#testing-cqrs-components)

---

## Why CQRS?

In many applications, the models used for reading data and the models used for
writing data have different needs:

* **Writes** must validate invariants, enforce business rules, and emit domain
  events.
* **Reads** must be fast, denormalized, and optimized for the UI or API
  consumer.

CQRS formalizes this split. Instead of a single service method that does
everything, you define explicit **Command** objects for writes and **Query**
objects for reads, each handled by a dedicated handler class. This leads to:

* **Clearer intent** -- every operation is an explicit, named object.
* **Simpler handlers** -- each handler does one thing.
* **Independent scaling** -- reads and writes can be optimized separately.
* **Natural audit trail** -- commands represent things that happened.

---

## Core Concepts

```
            +------------------+
            |     Mediator     |
            +--------+---------+
                     |
         +-----------+-----------+
         |                       |
   CommandHandler          QueryHandler
   (write operations)      (read operations)
         |                       |
    Command objects          Query objects
```

The `Mediator` is the central dispatcher. You register one handler per
command/query type. When you call `mediator.send(message)`, the mediator looks
up the handler for the message type, runs it through the middleware pipeline,
and returns the result.

---

## Commands

A `Command` represents a write operation -- an intent to change system state.
Commands inherit from `pyfly.cqrs.Command` and are typically defined as
dataclasses:

```python
from dataclasses import dataclass
from pyfly.cqrs import Command


@dataclass
class CreateOrderCommand(Command):
    customer_id: str
    items: list[dict]


@dataclass
class CancelOrderCommand(Command):
    order_id: str
    reason: str


@dataclass
class UpdateOrderStatusCommand(Command):
    order_id: str
    new_status: str
```

Commands should carry **all the data** the handler needs to perform the
operation. They are plain data objects with no behavior.

### Naming Convention

Use the imperative mood: `CreateOrder`, `CancelOrder`, `UpdateStatus`. The
suffix `Command` makes the intent explicit.

---

## Queries

A `Query` represents a read operation -- a request for data. Queries inherit
from `pyfly.cqrs.Query`:

```python
from dataclasses import dataclass
from pyfly.cqrs import Query


@dataclass
class GetOrderQuery(Query):
    order_id: str


@dataclass
class ListOrdersByCustomerQuery(Query):
    customer_id: str
    page: int = 1
    page_size: int = 20


@dataclass
class SearchOrdersQuery(Query):
    status: str | None = None
    date_from: str | None = None
    date_to: str | None = None
```

Queries carry the **criteria** for the read operation. They never modify state.

### Naming Convention

Use the declarative mood: `GetOrder`, `ListOrders`, `SearchOrders`. The suffix
`Query` distinguishes them from commands.

---

## CommandHandler

A `CommandHandler` processes a specific command type. It is a generic class
parameterized by the command type it handles:

```python
from pyfly.cqrs import CommandHandler


class CreateOrderHandler(CommandHandler[CreateOrderCommand]):

    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    async def handle(self, command: CreateOrderCommand) -> dict:
        order = Order(
            customer_id=command.customer_id,
            items=command.items,
            status="CREATED",
        )
        saved = await self._repo.save(order)
        return {"order_id": str(saved.id), "status": saved.status}
```

### Key Points

* Subclass `CommandHandler[T]` where `T` is your command type.
* Override the `async def handle(self, command: T) -> Any` method.
* The handler can return a value (e.g., the created entity's ID). The mediator
  passes it back to the caller.
* Inject dependencies through the constructor.

---

## QueryHandler

A `QueryHandler` processes a specific query type. It mirrors `CommandHandler`
but is intended for read operations:

```python
from pyfly.cqrs import QueryHandler


class GetOrderHandler(QueryHandler[GetOrderQuery]):

    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    async def handle(self, query: GetOrderQuery) -> dict | None:
        order = await self._repo.find_by_id(query.order_id)
        if order is None:
            return None
        return {
            "order_id": str(order.id),
            "customer_id": order.customer_id,
            "status": order.status,
            "items": order.items,
        }
```

### Key Points

* Subclass `QueryHandler[T]` where `T` is your query type.
* Override `async def handle(self, query: T) -> Any`.
* Query handlers should **never** modify state.

---

## Handler Decorators: @command_handler and @query_handler

The `@command_handler` and `@query_handler` decorators mark handler classes for
auto-discovery by the framework. They do not change the class behavior; they
add a metadata attribute that the container scans during startup.

```python
from pyfly.cqrs import command_handler, query_handler, CommandHandler, QueryHandler


@command_handler
class CreateOrderHandler(CommandHandler[CreateOrderCommand]):
    async def handle(self, command: CreateOrderCommand) -> dict:
        ...


@query_handler
class GetOrderHandler(QueryHandler[GetOrderQuery]):
    async def handle(self, query: GetOrderQuery) -> dict | None:
        ...
```

### What the Decorators Do

| Decorator          | Attribute Set                         | Value       |
|--------------------|---------------------------------------|-------------|
| `@command_handler` | `cls.__pyfly_handler_type__`          | `"command"` |
| `@query_handler`   | `cls.__pyfly_handler_type__`          | `"query"`   |

During context initialization, the framework scans all beans for classes with
`__pyfly_handler_type__` and automatically registers them with the `Mediator`.

You can also combine these decorators with `@service` for dependency injection:

```python
from pyfly.container import service

@command_handler
@service
class CreateOrderHandler(CommandHandler[CreateOrderCommand]):
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    async def handle(self, command: CreateOrderCommand) -> dict:
        ...
```

---

## The Mediator

The `Mediator` is the central dispatcher that routes commands and queries to
their registered handlers. It also manages the middleware pipeline.

```python
from pyfly.cqrs import Mediator

mediator = Mediator()
```

### Registering Handlers

Each command or query type maps to **exactly one** handler:

```python
# Create handler instances (typically done by the container)
create_handler = CreateOrderHandler(repo=order_repo)
get_handler = GetOrderHandler(repo=order_repo)
cancel_handler = CancelOrderHandler(repo=order_repo)

# Register
mediator.register_handler(CreateOrderCommand, create_handler)
mediator.register_handler(GetOrderQuery, get_handler)
mediator.register_handler(CancelOrderCommand, cancel_handler)
```

If you register two handlers for the same type, the second replaces the first.

### Dispatching Messages

Use `send()` for both commands and queries:

```python
# Send a command
result = await mediator.send(
    CreateOrderCommand(customer_id="cust-42", items=[{"sku": "A1", "qty": 2}])
)
print(result)  # {"order_id": "abc-123", "status": "CREATED"}

# Send a query
order = await mediator.send(GetOrderQuery(order_id="abc-123"))
print(order)   # {"order_id": "abc-123", "customer_id": "cust-42", ...}
```

The `send()` method:

1. Looks up the handler for `type(message)`.
2. Builds the middleware chain (innermost = handler, outermost = first
   middleware).
3. Invokes the chain with the message.
4. Returns the result.

### Error Handling

If no handler is registered for a message type, `send()` raises a `KeyError`:

```python
try:
    await mediator.send(UnknownCommand())
except KeyError as e:
    print(e)  # "No handler registered for UnknownCommand"
```

Exceptions raised by the handler (or middleware) propagate to the caller
naturally.

---

## Middleware Pipeline

Middleware allows you to wrap every command/query execution with cross-cutting
logic -- logging, metrics, authorization, validation, retry, etc.

### CqrsMiddleware Protocol

Any class that implements the following protocol can serve as middleware:

```python
from collections.abc import Awaitable, Callable
from typing import Any, Protocol


class CqrsMiddleware(Protocol):
    async def handle(
        self,
        message: Any,
        next_handler: Callable[..., Awaitable[Any]],
    ) -> Any: ...
```

The `message` parameter is the command or query being processed. The
`next_handler` is a callable that invokes the next middleware in the chain (or
the actual handler if this is the innermost middleware). You **must** call
`next_handler(message)` to continue the chain.

### LoggingMiddleware

A built-in middleware that logs before and after handler execution:

```python
from pyfly.cqrs import Mediator, LoggingMiddleware

logger = structlog.get_logger()
mediator = Mediator(middleware=[LoggingMiddleware(logger=logger)])
```

The `LoggingMiddleware` constructor accepts an optional `logger`. If provided,
it calls `logger.info()` with the message type name before and after handler
execution.

```
INFO  Handling CreateOrderCommand    message_type=CreateOrderCommand
INFO  Completed CreateOrderCommand   message_type=CreateOrderCommand
```

### MetricsMiddleware

A built-in middleware that increments a counter for every command/query
processed:

```python
from pyfly.cqrs import Mediator, MetricsMiddleware

mediator = Mediator(middleware=[MetricsMiddleware(registry=metrics_registry)])
```

The `MetricsMiddleware` constructor accepts an optional `registry`. If
provided, it creates a counter named `cqrs_messages_total` and increments it
on every `send()` call.

### Writing Custom Middleware

Custom middleware follows the same protocol. Here are two practical examples:

#### Authorization Middleware

```python
class AuthorizationMiddleware:
    """Check permissions before handler execution."""

    def __init__(self, auth_service: AuthService) -> None:
        self._auth = auth_service

    async def handle(self, message: Any, next_handler: Callable[..., Awaitable[Any]]) -> Any:
        # Check permissions for write operations
        if isinstance(message, Command):
            await self._auth.check_permission(type(message).__name__)

        return await next_handler(message)
```

#### Timing Middleware

```python
import time


class TimingMiddleware:
    """Measure handler execution time."""

    async def handle(self, message: Any, next_handler: Callable[..., Awaitable[Any]]) -> Any:
        start = time.perf_counter()
        try:
            return await next_handler(message)
        finally:
            elapsed = time.perf_counter() - start
            print(f"{type(message).__name__} took {elapsed:.3f}s")
```

#### Validation Middleware

```python
class ValidationMiddleware:
    """Validate commands before they reach the handler."""

    async def handle(self, message: Any, next_handler: Callable[..., Awaitable[Any]]) -> Any:
        if isinstance(message, Command) and hasattr(message, "validate"):
            message.validate()  # Raises ValueError on invalid state

        return await next_handler(message)
```

### Middleware Execution Order

Middleware is registered as a list in the `Mediator` constructor. The **first**
middleware in the list is the **outermost** wrapper:

```python
mediator = Mediator(middleware=[
    AuthorizationMiddleware(auth),   # 1st: outermost -- runs first on the way in
    LoggingMiddleware(logger),       # 2nd: middle
    MetricsMiddleware(registry),     # 3rd: innermost -- closest to the handler
])
```

The execution flow for `mediator.send(command)` is:

```
AuthorizationMiddleware.handle()
  -> LoggingMiddleware.handle()
       -> MetricsMiddleware.handle()
            -> actual handler.handle()
            <- returns result
       <- returns result
  <- returns result
<- returns result
```

This is the standard onion/decorator pattern: each middleware wraps the next,
and they unwind in reverse order.

---

## Complete Example: Order Management

This example brings together all CQRS components in a realistic order
management scenario, including commands, queries, handlers, middleware, and a
REST controller.

```python
from dataclasses import dataclass
from typing import Any

from pyfly.container import service, configuration, bean, rest_controller
from pyfly.cqrs import (
    Command,
    Query,
    CommandHandler,
    QueryHandler,
    Mediator,
    LoggingMiddleware,
    MetricsMiddleware,
    command_handler,
    query_handler,
)
from pyfly.web import request_mapping, get_mapping, post_mapping, Body


# ---------------------------------------------------------------------------
# Commands & Queries
# ---------------------------------------------------------------------------

@dataclass
class CreateOrderCommand(Command):
    customer_id: str
    items: list[dict]


@dataclass
class CancelOrderCommand(Command):
    order_id: str
    reason: str


@dataclass
class GetOrderQuery(Query):
    order_id: str


@dataclass
class ListOrdersByCustomerQuery(Query):
    customer_id: str
    page: int = 1
    page_size: int = 20


# ---------------------------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------------------------

@command_handler
@service
class CreateOrderHandler(CommandHandler[CreateOrderCommand]):
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    async def handle(self, command: CreateOrderCommand) -> dict:
        order = await self._repo.save(
            Order(customer_id=command.customer_id, items=command.items, status="CREATED")
        )
        return {"order_id": str(order.id), "status": order.status}


@command_handler
@service
class CancelOrderHandler(CommandHandler[CancelOrderCommand]):
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    async def handle(self, command: CancelOrderCommand) -> dict:
        order = await self._repo.find_by_id(command.order_id)
        if order is None:
            raise ValueError(f"Order {command.order_id} not found")
        order.status = "CANCELLED"
        order.cancel_reason = command.reason
        await self._repo.save(order)
        return {"order_id": command.order_id, "status": "CANCELLED"}


# ---------------------------------------------------------------------------
# Query Handlers
# ---------------------------------------------------------------------------

@query_handler
@service
class GetOrderHandler(QueryHandler[GetOrderQuery]):
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    async def handle(self, query: GetOrderQuery) -> dict | None:
        order = await self._repo.find_by_id(query.order_id)
        if order is None:
            return None
        return {"order_id": str(order.id), "status": order.status, "items": order.items}


@query_handler
@service
class ListOrdersByCustomerHandler(QueryHandler[ListOrdersByCustomerQuery]):
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    async def handle(self, query: ListOrdersByCustomerQuery) -> dict:
        orders = await self._repo.find_by_customer(
            query.customer_id, page=query.page, page_size=query.page_size
        )
        return {"orders": orders, "page": query.page, "page_size": query.page_size}


# ---------------------------------------------------------------------------
# Mediator Configuration
# ---------------------------------------------------------------------------

@configuration
class CqrsConfig:
    @bean
    def mediator(
        self,
        create_handler: CreateOrderHandler,
        cancel_handler: CancelOrderHandler,
        get_handler: GetOrderHandler,
        list_handler: ListOrdersByCustomerHandler,
    ) -> Mediator:
        m = Mediator(middleware=[LoggingMiddleware(), MetricsMiddleware()])
        m.register_handler(CreateOrderCommand, create_handler)
        m.register_handler(CancelOrderCommand, cancel_handler)
        m.register_handler(GetOrderQuery, get_handler)
        m.register_handler(ListOrdersByCustomerQuery, list_handler)
        return m


# ---------------------------------------------------------------------------
# REST Controller
# ---------------------------------------------------------------------------

@dataclass
class CreateOrderRequest:
    customer_id: str
    items: list[dict]


@rest_controller
@request_mapping("/api/orders")
class OrderController:
    def __init__(self, mediator: Mediator) -> None:
        self._mediator = mediator

    @post_mapping("/", status_code=201)
    async def create_order(self, body: Body[CreateOrderRequest]) -> dict:
        return await self._mediator.send(
            CreateOrderCommand(customer_id=body.customer_id, items=body.items)
        )

    @get_mapping("/{order_id}")
    async def get_order(self, order_id: str) -> dict:
        result = await self._mediator.send(GetOrderQuery(order_id=order_id))
        if result is None:
            raise ResourceNotFoundException("Order not found")
        return result

    @get_mapping("/customer/{customer_id}")
    async def list_orders(self, customer_id: str, page: int = 1) -> dict:
        return await self._mediator.send(
            ListOrdersByCustomerQuery(customer_id=customer_id, page=page)
        )
```

---

## Testing CQRS Components

Because commands, queries, and handlers are plain Python objects, they are easy
to test in isolation.

### Testing a Handler Directly

```python
import pytest


@pytest.mark.asyncio
async def test_create_order_handler() -> None:
    repo = InMemoryOrderRepository()
    handler = CreateOrderHandler(repo=repo)

    result = await handler.handle(
        CreateOrderCommand(customer_id="cust-1", items=[{"sku": "A", "qty": 2}])
    )

    assert result["status"] == "CREATED"
    assert "order_id" in result
    assert len(repo.orders) == 1
```

### Testing Through the Mediator

```python
@pytest.mark.asyncio
async def test_mediator_dispatches_to_correct_handler() -> None:
    repo = InMemoryOrderRepository()
    create_handler = CreateOrderHandler(repo=repo)
    get_handler = GetOrderHandler(repo=repo)

    mediator = Mediator()
    mediator.register_handler(CreateOrderCommand, create_handler)
    mediator.register_handler(GetOrderQuery, get_handler)

    # Create an order via command
    created = await mediator.send(
        CreateOrderCommand(customer_id="cust-1", items=[{"sku": "A", "qty": 1}])
    )

    # Retrieve it via query
    fetched = await mediator.send(GetOrderQuery(order_id=created["order_id"]))

    assert fetched is not None
    assert fetched["order_id"] == created["order_id"]
    assert fetched["status"] == "CREATED"
```

### Testing Middleware

```python
@pytest.mark.asyncio
async def test_middleware_wraps_handler() -> None:
    calls: list[str] = []

    class TrackingMiddleware:
        async def handle(self, message, next_handler):
            calls.append("before")
            result = await next_handler(message)
            calls.append("after")
            return result

    repo = InMemoryOrderRepository()
    handler = CreateOrderHandler(repo=repo)

    mediator = Mediator(middleware=[TrackingMiddleware()])
    mediator.register_handler(CreateOrderCommand, handler)

    await mediator.send(CreateOrderCommand(customer_id="c", items=[]))

    assert calls == ["before", "after"]
```

### Testing Unknown Message Type

```python
@pytest.mark.asyncio
async def test_unregistered_message_raises_key_error() -> None:
    mediator = Mediator()

    @dataclass
    class UnknownCommand(Command):
        pass

    with pytest.raises(KeyError, match="No handler registered for UnknownCommand"):
        await mediator.send(UnknownCommand())
```
