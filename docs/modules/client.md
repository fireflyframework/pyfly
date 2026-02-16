# HTTP Client Guide

Build resilient service-to-service HTTP communication with the PyFly client
module, featuring circuit breakers, retry policies, and declarative clients.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Declarative Clients](#declarative-http-client)
   - [@service_client Decorator](#service_client-decorator)
   - [@http_client Decorator](#http_client-decorator)
   - [Method Decorators: @get, @post, @put, @delete, @patch](#method-decorators)
   - [Path Parameter Interpolation](#path-parameter-interpolation)
   - [Query Parameters and Request Bodies](#query-parameters-and-request-bodies)
3. [CircuitBreaker](#circuitbreaker)
   - [States](#states)
   - [State Transitions](#state-transitions)
   - [Constructor Parameters](#constructor-parameters)
   - [The call() Method](#the-call-method)
   - [Standalone Usage](#standalone-usage)
4. [RetryPolicy](#retrypolicy)
   - [Constructor Parameters](#retrypolicy-constructor-parameters)
   - [Exponential Backoff Algorithm](#exponential-backoff-algorithm)
   - [The execute() Method](#the-execute-method)
   - [Standalone Usage](#retrypolicy-standalone-usage)
4. [HttpClientPort](#httpclientport)
5. [HttpClientBeanPostProcessor](#httpclientbeanpostprocessor)
   - [How Wiring Works](#how-wiring-works)
   - [Custom Client Factory](#custom-client-factory)
6. [Configuration](#configuration)
7. [Complete Example](#complete-example)

---

## Introduction

In a microservice architecture, services communicate over HTTP. These network
calls are inherently unreliable: services go down, networks partition, and
response times spike. The PyFly client module provides resilient HTTP clients
through two complementary approaches:

- **Declarative** (`@http_client` / `@service_client`): An interface-based
  approach where you define method signatures and PyFly generates the HTTP
  implementation at startup. This is the recommended approach.
- **Resilience primitives** (`CircuitBreaker`, `RetryPolicy`): Composable
  building blocks for circuit breakers and retry policies.

Both approaches build on the same `HttpClientPort` abstraction, making it
straightforward to test with mocks or swap HTTP libraries.

All public types are available from a single import:

```python
from pyfly.client import (
    CircuitBreaker,
    CircuitState,
    RetryPolicy,
    http_client,
    service_client,
    get,
    post,
    put,
    delete,
    patch,
    HttpClientPort,
    HttpClientBeanPostProcessor,
)
```

---

## CircuitBreaker

The circuit breaker prevents cascading failures by tracking consecutive errors
and stopping calls to a failing dependency. It follows the classic three-state
model.

### States

```python
from pyfly.client import CircuitState

CircuitState.CLOSED     # Normal operation -- requests flow through
CircuitState.OPEN       # Failing -- requests are rejected immediately
CircuitState.HALF_OPEN  # Probing -- one request allowed to test recovery
```

The `CircuitState` enum uses `auto()` values.

### State Transitions

```
                 success
    +---------+----------+---------+
    |         |          |         |
    v         |          v         |
 CLOSED ------+----> OPEN -----> HALF_OPEN
    ^    failure_threshold    recovery_timeout
    |    consecutive              |
    |    failures                 |
    +-------- success -----------+
              (probe succeeds)

    HALF_OPEN --failure--> OPEN
```

**CLOSED -> OPEN**: After `failure_threshold` consecutive failures, the
circuit opens. All subsequent calls raise `CircuitBreakerException`
immediately.

**OPEN -> HALF_OPEN**: After `recovery_timeout` elapses, the circuit
transitions to half-open. The state property computes this lazily using
`time.monotonic()` -- there is no background timer.

**HALF_OPEN -> CLOSED**: If the probe request succeeds, the failure counter
resets to zero and the circuit closes.

**HALF_OPEN -> OPEN**: If the probe request fails, the circuit reopens and
the recovery timeout starts again.

### Constructor Parameters

```python
from datetime import timedelta
from pyfly.client import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,                    # Open after 5 consecutive failures
    recovery_timeout=timedelta(seconds=30), # Wait 30s before probing
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `failure_threshold` | `int` | `5` | Consecutive failures before opening the circuit. |
| `recovery_timeout` | `timedelta` | `30s` | Time to wait in OPEN state before allowing a probe. |

### The call() Method

`call()` is an async method that executes a function through the circuit
breaker:

```python
result = await breaker.call(some_async_function, arg1, arg2)
```

Internally:

1. Check the current state.
2. If `OPEN`, raise `CircuitBreakerException` immediately.
3. If `CLOSED` or `HALF_OPEN`, execute the function.
4. On success: reset failure count to zero, set state to `CLOSED`,
   clear the last failure time.
5. On exception (other than `CircuitBreakerException`): increment failure
   count, record failure time. If the count reaches the threshold, set state
   to `OPEN`. Re-raise the original exception.

`CircuitBreakerException` itself is never counted as a failure -- it is
re-raised directly without recording.

### Standalone Usage

You can use `CircuitBreaker` independently of the HTTP client:

```python
from pyfly.client import CircuitBreaker
from pyfly.kernel.exceptions import CircuitBreakerException

breaker = CircuitBreaker(failure_threshold=3)

async def call_external_api():
    try:
        return await breaker.call(http_client.get, "/health")
    except CircuitBreakerException:
        return {"status": "circuit open, using cached data"}
```

---

## RetryPolicy

`RetryPolicy` implements retry logic with exponential backoff for transient
failures.

### RetryPolicy Constructor Parameters

```python
from datetime import timedelta
from pyfly.client import RetryPolicy

policy = RetryPolicy(
    max_attempts=3,
    base_delay=timedelta(seconds=1),
    retry_on=(ConnectionError, TimeoutError),
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `max_attempts` | `int` | `3` | Total attempts (including the first). |
| `base_delay` | `timedelta` | `1s` | Base delay between retries. Doubled each attempt. |
| `retry_on` | `tuple[type[Exception], ...]` | `(Exception,)` | Exception types that trigger a retry. |

### Exponential Backoff Algorithm

The delay between retries follows an exponential pattern:

```
delay = base_delay * (2 ** attempt)
```

For `base_delay=1s` and `max_attempts=4`:

| Attempt | Delay before retry |
|---|---|
| 1 (first try) | -- |
| 2 (1st retry) | 1s (`1 * 2^0`) |
| 3 (2nd retry) | 2s (`1 * 2^1`) |
| 4 (3rd retry) | 4s (`1 * 2^2`) |

The delay is applied via `asyncio.sleep()`. There is no jitter by default.

### The execute() Method

`execute()` runs a callable with the retry policy:

```python
result = await policy.execute(some_async_function, arg1, arg2)
```

Behavior:

1. Call the function.
2. If it succeeds, return the result immediately.
3. If it raises an exception matching `retry_on`, sleep for the backoff delay
   and try again.
4. If it raises an exception **not** matching `retry_on`, re-raise immediately
   (no retry).
5. If all attempts are exhausted, raise the last exception.

### RetryPolicy Standalone Usage

```python
from datetime import timedelta
from pyfly.client import RetryPolicy

retry = RetryPolicy(
    max_attempts=3,
    base_delay=timedelta(milliseconds=500),
    retry_on=(ConnectionError,),
)

# Retry a flaky operation
result = await retry.execute(flaky_api_call, "/data")
```

---

## Declarative HTTP Client

The declarative approach lets you define an HTTP client as a Python class with
method stubs. PyFly generates the HTTP implementation at startup.

Two decorators are available:

| Decorator | Resilience | Use Case |
|-----------|-----------|----------|
| `@service_client` | Circuit breaker + retry | Production service-to-service calls |
| `@http_client` | None | Lightweight clients, testing |

### @service_client Decorator

Mark a class as a **resilient** declarative HTTP client with built-in circuit
breaker and retry:

```python
from pyfly.client import service_client, get, post

@service_client(
    base_url="http://payment-service:8080",
    circuit_breaker=True,
    retry=3,
    circuit_breaker_failure_threshold=5,
    circuit_breaker_recovery_timeout=60.0,
    retry_base_delay=1.0,
)
class PaymentClient:
    @get("/payments/{payment_id}")
    async def get_payment(self, payment_id: str) -> dict:
        ...

    @post("/payments")
    async def create_payment(self, body: dict) -> dict:
        ...
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | `str` | *required* | Base URL for all requests |
| `retry` | `int \| bool` | `True` | `True` for default retry, `int` for max attempts, `False` to disable |
| `circuit_breaker` | `bool` | `True` | Enable circuit breaker wrapping |
| `retry_base_delay` | `float \| None` | `None` | Override base delay (seconds) between retries |
| `circuit_breaker_failure_threshold` | `int \| None` | `None` | Override failures before opening circuit |
| `circuit_breaker_recovery_timeout` | `float \| None` | `None` | Override recovery timeout (seconds) |

`@service_client` sets the same metadata as `@http_client` plus:

| Attribute | Value |
|-----------|-------|
| `__pyfly_service_client__` | `True` |
| `__pyfly_resilience__` | Dict with retry/circuit breaker configuration |

The `HttpClientBeanPostProcessor` reads the resilience configuration and wraps
each method with the appropriate circuit breaker and retry policies at startup.

### @http_client Decorator

Mark a class as a declarative HTTP client (no resilience). Equivalent to
`@service_client(base_url, retry=False, circuit_breaker=False)`:

```python
from pyfly.client import http_client, get, post, delete

@http_client(base_url="http://user-service:8080")
class UserClient:
    @get("/users/{user_id}")
    async def get_user(self, user_id: str) -> dict:
        ...

    @post("/users")
    async def create_user(self, body: dict) -> dict:
        ...

    @delete("/users/{user_id}")
    async def delete_user(self, user_id: str) -> None:
        ...
```

The `@http_client` decorator sets the following metadata on the class:

| Attribute | Value |
|---|---|
| `__pyfly_http_client__` | `True` |
| `__pyfly_http_base_url__` | The base URL string |
| `__pyfly_injectable__` | `True` |
| `__pyfly_stereotype__` | `"component"` |
| `__pyfly_scope__` | `Scope.SINGLETON` |

This means `@http_client` classes are automatically registered as singleton
beans in the PyFly dependency injection container.

### Method Decorators

Each HTTP method decorator marks a method with an HTTP verb and path template:

```python
@get("/users")           # GET /users
@post("/users")          # POST /users
@put("/users/{id}")      # PUT /users/:id
@delete("/users/{id}")   # DELETE /users/:id
@patch("/users/{id}")    # PATCH /users/:id
```

The decorated methods are initially placeholder stubs that raise
`NotImplementedError` with a message like `"UserClient.get_user has not been
wired by HttpClientBeanPostProcessor"`. The `HttpClientBeanPostProcessor`
replaces them with real implementations at startup.

Each stub carries metadata attributes:

| Attribute | Value |
|---|---|
| `__pyfly_http_method__` | The HTTP method string (`"GET"`, `"POST"`, etc.) |
| `__pyfly_http_path__` | The path template string |

### Path Parameter Interpolation

Parameters in the method signature that match `{placeholder}` patterns in the
path template are automatically interpolated:

```python
@http_client(base_url="http://api:8080")
class OrderClient:
    @get("/orders/{order_id}/items/{item_id}")
    async def get_item(self, order_id: str, item_id: str) -> dict:
        ...

# At runtime: GET http://api:8080/orders/abc/items/xyz
result = await client.get_item("abc", "xyz")
```

### Query Parameters and Request Bodies

Parameters that do not match a path placeholder are handled as follows:

- For **GET** and **DELETE** requests: remaining parameters become query
  string parameters.
- For **POST**, **PUT**, and **PATCH** requests: a parameter named `body` is
  serialized as JSON in the request body. Other remaining parameters become
  query string parameters.

```python
@http_client(base_url="http://api:8080")
class ProductClient:
    @get("/products")
    async def search(self, category: str, page: int = 1) -> list:
        ...
    # GET /products?category=electronics&page=1

    @post("/products")
    async def create(self, body: dict) -> dict:
        ...
    # POST /products  with JSON body

    @put("/products/{product_id}")
    async def update(self, product_id: str, body: dict) -> dict:
        ...
    # PUT /products/123  with JSON body
```

All generated method implementations return `response.json()`, parsing the
response body as JSON.

---

## HttpClientPort

`HttpClientPort` is a `Protocol` (runtime-checkable) that defines the abstract
interface for HTTP communication:

```python
from pyfly.client import HttpClientPort

@runtime_checkable
class HttpClientPort(Protocol):
    async def request(self, method: str, url: str, **kwargs: Any) -> Any: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
```

This abstraction allows:

- **Testing**: Mock the port to return canned responses.
- **Flexibility**: Swap `httpx` for `aiohttp` or any other HTTP library.
- **Hexagonal architecture**: The core domain code never depends on a specific
  HTTP library.

The default implementation is `HttpxClientAdapter`, which wraps
`httpx.AsyncClient`. It accepts `base_url`, `timeout`, and `headers` in its
constructor.

### Implementing a Custom Adapter

```python
import aiohttp
from datetime import timedelta


class AioHttpAdapter:
    """HttpClientPort backed by aiohttp."""

    def __init__(self, base_url: str, timeout: timedelta = timedelta(seconds=30)):
        self._base_url = base_url
        self._session: aiohttp.ClientSession | None = None
        self._timeout = aiohttp.ClientTimeout(total=timeout.total_seconds())

    async def _ensure_session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession(
                base_url=self._base_url,
                timeout=self._timeout,
            )

    async def request(self, method: str, url: str, **kwargs):
        await self._ensure_session()
        async with self._session.request(method, url, **kwargs) as resp:
            return await resp.json()

    async def start(self) -> None:
        await self._ensure_session()

    async def stop(self) -> None:
        if self._session:
            await self._session.close()
```

---

## HttpClientBeanPostProcessor

`HttpClientBeanPostProcessor` is a bean post-processor that wires declarative
`@http_client` classes at startup. It replaces the stub methods (which raise
`NotImplementedError`) with real HTTP implementations.

### How Wiring Works

The post-processor has two lifecycle hooks:

1. **before_init(bean, bean_name)**: Returns the bean unchanged (no-op).
2. **after_init(bean, bean_name)**: If the bean's class has
   `__pyfly_http_client__ = True`, it:
   - Creates an `HttpClientPort` instance using the factory (default:
     `HttpxClientAdapter`) with the class's `__pyfly_http_base_url__`.
   - Iterates over all class attributes looking for methods with
     `__pyfly_http_method__` metadata.
   - For each stub method, calls `_make_method_impl()` to generate a real
     implementation.
   - Binds the generated implementation to the bean instance using the
     descriptor protocol (`__get__`).

The generated implementation:

1. Uses `inspect.signature()` to bind the caller's arguments.
2. Resolves path variables by replacing `{placeholder}` patterns with the
   corresponding argument values.
3. Separates remaining parameters into query parameters or JSON body (for
   POST/PUT/PATCH, the `body` parameter is sent as `json`).
4. Calls `client.request(method, path, **kwargs)`.
5. Returns `response.json()`.

### Custom Client Factory

You can provide a custom factory function to control how HTTP clients are
created:

```python
from pyfly.client import HttpClientBeanPostProcessor

def my_factory(base_url: str):
    return AioHttpAdapter(base_url=base_url)

processor = HttpClientBeanPostProcessor(http_client_factory=my_factory)
```

The factory receives the base URL and must return an object implementing the
`HttpClientPort` protocol.

---

## Configuration

HTTP client settings can be configured in `pyfly.yaml`:

```yaml
pyfly:
  client:
    default:
      timeout: 30s
      connect-timeout: 5s
    circuit-breaker:
      failure-threshold: 5
      recovery-timeout: 30s
    retry:
      max-attempts: 3
      base-delay: 1s
```

| Key | Description | Default |
|---|---|---|
| `pyfly.client.default.timeout` | Default request timeout | `30s` |
| `pyfly.client.default.connect-timeout` | TCP connection timeout | `5s` |
| `pyfly.client.circuit-breaker.failure-threshold` | Consecutive failures to open circuit | `5` |
| `pyfly.client.circuit-breaker.recovery-timeout` | Time before probing after open | `30s` |
| `pyfly.client.retry.max-attempts` | Total attempts including first | `3` |
| `pyfly.client.retry.base-delay` | Base delay for exponential backoff | `1s` |

---

## Complete Example

### Declarative Client

```python
from pyfly.client import http_client, get, post, put, delete


@http_client(base_url="http://inventory-service:8080")
class InventoryClient:
    """Declarative HTTP client for the inventory service.

    Method implementations are generated at startup by
    HttpClientBeanPostProcessor. Just define the signatures.
    """

    @get("/products/{product_id}")
    async def get_product(self, product_id: str) -> dict:
        """GET /products/:product_id"""
        ...

    @get("/products")
    async def search_products(self, category: str, in_stock: bool = True) -> list:
        """GET /products?category=...&in_stock=..."""
        ...

    @post("/products")
    async def create_product(self, body: dict) -> dict:
        """POST /products with JSON body"""
        ...

    @put("/products/{product_id}")
    async def update_product(self, product_id: str, body: dict) -> dict:
        """PUT /products/:product_id with JSON body"""
        ...

    @delete("/products/{product_id}")
    async def delete_product(self, product_id: str) -> None:
        """DELETE /products/:product_id"""
        ...


# Usage (after ApplicationContext startup wires the client):
@service
class CatalogService:
    def __init__(self, inventory: InventoryClient):
        self.inventory = inventory

    async def get_catalog_page(self, category: str) -> list:
        products = await self.inventory.search_products(
            category=category, in_stock=True
        )
        return products
```

### Testing with a Mock HttpClientPort

```python
from unittest.mock import AsyncMock
from pyfly.client import HttpClientPort


async def test_catalog_service():
    # Create a mock HTTP client
    mock_http = AsyncMock(spec=HttpClientPort)
    mock_http.request.return_value = [{"id": "1", "name": "Widget"}]

    # Inject the mock into your service
    service = CatalogService(inventory=mock_http)
    products = await service.get_catalog_page("widgets")

    assert len(products) == 1
    mock_http.request.assert_called_once()
```

This demonstrates the value of the `HttpClientPort` abstraction: your tests
never make real HTTP calls, yet they exercise the full client interface.

---

## Adapters

- [HTTPX Adapter](../adapters/httpx.md) — Setup, configuration reference, and adapter-specific features for the HTTPX HTTP client backend
