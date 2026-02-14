# Web Layer Guide

The PyFly web layer provides enterprise-grade HTTP routing, controller registration, parameter binding, middleware, exception handling, CORS, security headers, and OpenAPI documentation. It follows a hexagonal (ports-and-adapters) architecture: the framework-agnostic core defines decorators, parameter types, and configuration dataclasses, while a pluggable adapter layer (Starlette by default) handles the actual HTTP server integration.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [REST Controllers](#rest-controllers)
  - [Defining a Controller](#defining-a-controller)
  - [@rest_controller Stereotype](#rest_controller-stereotype)
  - [@request_mapping: Class-Level Base Path](#request_mapping-class-level-base-path)
- [HTTP Method Mappings](#http-method-mappings)
  - [@get_mapping](#get_mapping)
  - [@post_mapping](#post_mapping)
  - [@put_mapping](#put_mapping)
  - [@delete_mapping](#delete_mapping)
  - [@patch_mapping](#patch_mapping)
  - [Parameters Reference](#parameters-reference)
- [Request Parameter Binding](#request-parameter-binding)
  - [PathVar\[T\] -- Path Variables](#pathvart----path-variables)
  - [QueryParam\[T\] -- Query Parameters](#queryparamt----query-parameters)
  - [Body\[T\] -- Request Body](#bodyt----request-body)
  - [Header\[T\] -- HTTP Headers](#headert----http-headers)
  - [Cookie\[T\] -- Cookies](#cookiet----cookies)
  - [Type Coercion](#type-coercion)
- [Response Handling](#response-handling)
  - [Return Value Conversion](#return-value-conversion)
  - [handle_return_value()](#handle_return_value)
- [Exception Handling](#exception-handling)
  - [Controller-Level Exception Handlers](#controller-level-exception-handlers)
  - [Global Exception Handler](#global-exception-handler)
  - [Exception-to-Status Mapping](#exception-to-status-mapping)
  - [Exception Converters](#exception-converters)
- [Middleware](#middleware)
  - [TransactionIdMiddleware](#transactionidmiddleware)
  - [RequestLoggingMiddleware](#requestloggingmiddleware)
  - [SecurityHeadersMiddleware](#securityheadersmiddleware)
  - [Custom Middleware](#custom-middleware)
- [CORS Configuration](#cors-configuration)
- [Security Headers](#security-headers)
- [OpenAPI and Swagger Documentation](#openapi-and-swagger-documentation)
  - [Automatic Generation](#automatic-generation)
  - [Swagger UI](#swagger-ui)
  - [ReDoc](#redoc)
  - [OpenAPIGenerator Internals](#openapigenerator-internals)
- [Application Factory: create_app()](#application-factory-create_app)
  - [Full Parameter Reference](#full-parameter-reference)
  - [What create_app() Does](#what-create_app-does)
- [ControllerRegistrar](#controllerregistrar)
  - [Route Collection](#route-collection)
  - [Route Metadata for OpenAPI](#route-metadata-for-openapi)
  - [Exception Handler Discovery](#exception-handler-discovery)
- [ParameterResolver](#parameterresolver)
- [WebServerPort](#webserverport)
- [Complete CRUD Example](#complete-crud-example)

---

## Architecture Overview

PyFly's web layer is organized into three tiers:

1. **Framework-agnostic core** (`pyfly.web`): Decorators (`@get_mapping`, `@post_mapping`, etc.), parameter binding types (`PathVar`, `QueryParam`, `Body`, `Header`, `Cookie`), configuration dataclasses (`CORSConfig`, `SecurityHeadersConfig`), and the `@exception_handler` decorator. These contain no HTTP-framework-specific code and could be backed by any ASGI or WSGI framework.

2. **Port interfaces** (`pyfly.web.ports`): The `WebServerPort` protocol defines the contract that any web server adapter must implement, ensuring that the application layer never depends directly on Starlette, Flask, or any other framework.

3. **Starlette adapter** (`pyfly.web.adapters.starlette`): The default implementation that translates the framework-agnostic decorators and types into Starlette routes, middleware, and request handling. This includes the `ControllerRegistrar`, `ParameterResolver`, response handler, error handler, and OpenAPI endpoint generators.

For convenience, the top-level `pyfly.web` package re-exports both the core types and the Starlette adapter, so most applications need only a single import:

```python
from pyfly.web import (
    create_app, get_mapping, post_mapping, put_mapping, patch_mapping,
    delete_mapping, request_mapping, exception_handler,
    Body, PathVar, QueryParam, Header, Cookie,
    CORSConfig, SecurityHeadersConfig,
    ControllerRegistrar, RequestLoggingMiddleware,
    SecurityHeadersMiddleware, handle_return_value,
)
```

---

## REST Controllers

### Defining a Controller

A REST controller in PyFly is a plain Python class decorated with `@rest_controller` and `@request_mapping`. The framework discovers it automatically from the DI container and registers its handler methods as HTTP routes.

```python
from pyfly.container import rest_controller
from pyfly.web import request_mapping, get_mapping, post_mapping, Body, PathVar


@rest_controller
@request_mapping("/api/orders")
class OrderController:

    def __init__(self, order_service: OrderService) -> None:
        self._service = order_service

    @get_mapping("/")
    async def list_orders(self) -> list[dict]:
        return await self._service.find_all()

    @get_mapping("/{order_id}")
    async def get_order(self, order_id: PathVar[str]) -> dict:
        return await self._service.find_by_id(order_id)

    @post_mapping("/", status_code=201)
    async def create_order(self, body: Body[CreateOrderRequest]) -> dict:
        return await self._service.create(body)
```

### @rest_controller Stereotype

`@rest_controller` is a stereotype decorator from `pyfly.container`. It marks the class as both a DI-managed bean and a REST controller. Internally it sets:

- `__pyfly_injectable__ = True` -- registers the class in the DI container
- `__pyfly_stereotype__ = "rest_controller"` -- identifies the class for route auto-discovery

It supports all standard stereotype options:

```python
@rest_controller                              # Simple form
@rest_controller(name="orderCtrl")            # Named bean
@rest_controller(scope=Scope.SINGLETON)       # Custom scope
@rest_controller(profile="api")               # Profile-conditional
```

### @request_mapping: Class-Level Base Path

`@request_mapping(path)` sets the base URL path for all handler methods in the controller. The path is combined with each method's path to form the full route.

```python
@request_mapping("/api/v2/orders")
class OrderController:
    @get_mapping("/{id}")        # Full path: /api/v2/orders/{id}
    async def get(self, id: PathVar[str]): ...

    @get_mapping("/")            # Full path: /api/v2/orders/
    async def list_all(self): ...
```

Trailing slashes on the base path are automatically stripped to prevent double-slash issues.

---

## HTTP Method Mappings

PyFly provides five HTTP method decorators, each created by the internal `_make_method_mapping()` factory. Every decorator accepts an optional relative path and an optional `status_code`.

### @get_mapping

Map a handler to HTTP GET requests. Used for read operations.

```python
@get_mapping("/")
async def list_items(self) -> list[dict]:
    return await self._service.find_all()

@get_mapping("/{item_id}")
async def get_item(self, item_id: PathVar[str]) -> dict:
    return await self._service.find_by_id(item_id)
```

### @post_mapping

Map a handler to HTTP POST requests. Typically used for create operations.

```python
@post_mapping("/", status_code=201)
async def create_item(self, body: Body[CreateItemRequest]) -> dict:
    return await self._service.create(body)
```

### @put_mapping

Map a handler to HTTP PUT requests. Used for full-replacement updates.

```python
@put_mapping("/{item_id}")
async def replace_item(self, item_id: PathVar[str], body: Body[UpdateItemRequest]) -> dict:
    return await self._service.replace(item_id, body)
```

### @delete_mapping

Map a handler to HTTP DELETE requests.

```python
@delete_mapping("/{item_id}", status_code=204)
async def delete_item(self, item_id: PathVar[str]) -> None:
    await self._service.delete(item_id)
```

### @patch_mapping

Map a handler to HTTP PATCH requests. Used for partial updates.

```python
@patch_mapping("/{item_id}")
async def update_item(self, item_id: PathVar[str], body: Body[PatchItemRequest]) -> dict:
    return await self._service.patch(item_id, body)
```

### Parameters Reference

All five decorators share the same parameters:

| Parameter     | Type  | Default | Description                                                          |
|---------------|-------|---------|----------------------------------------------------------------------|
| `path`        | `str` | `""`    | Relative path appended to the `@request_mapping` base path           |
| `status_code` | `int` | `200`   | HTTP status code for the response                                    |

Path parameters use `{name}` syntax in the path string: `@get_mapping("/{order_id}")`.

Internally, each decorator stores a `__pyfly_mapping__` dict on the function with keys `"method"`, `"path"`, and `"status_code"`.

---

## Request Parameter Binding

PyFly uses generic type annotations to bind handler parameters from the HTTP request. The `ParameterResolver` inspects handler signatures at startup and builds a resolution plan that is executed at request time.

### PathVar[T] -- Path Variables

Extracts a value from the URL path. The parameter name must match a `{placeholder}` in the route path.

```python
@get_mapping("/{order_id}")
async def get_order(self, order_id: PathVar[str]) -> dict:
    # order_id is extracted from the URL, e.g., "/api/orders/abc-123"
    return await self._service.find_by_id(order_id)
```

With type conversion:

```python
@get_mapping("/{order_id}")
async def get_order(self, order_id: PathVar[int]) -> dict:
    # Automatically converts the path segment to int
    return await self._service.find_by_id(order_id)
```

If the path variable is missing and no default is provided, a `ValueError` is raised with the message `"Missing path variable: {name}"`.

### QueryParam[T] -- Query Parameters

Extracts a value from the URL query string. Supports default values and optional parameters.

```python
@get_mapping("/")
async def list_orders(
    self,
    page: QueryParam[int] = 1,
    size: QueryParam[int] = 20,
    status: QueryParam[str] = None,
) -> dict:
    # GET /api/orders?page=2&size=10&status=active
    return await self._service.find_all(page=page, size=size, status=status)
```

- If the query parameter is not present and a default is provided, the default is used.
- If the query parameter is not present and no default is provided, `None` is returned.
- The raw string value is automatically coerced to the annotated type `T`.

### Body[T] -- Request Body

Deserializes the JSON request body. When `T` is a Pydantic `BaseModel`, automatic validation is applied via `model_validate_json()`.

```python
from pydantic import BaseModel


class CreateOrderRequest(BaseModel):
    product_id: str
    quantity: int
    customer_id: str


@post_mapping("/", status_code=201)
async def create_order(self, body: Body[CreateOrderRequest]) -> dict:
    # body is a fully validated CreateOrderRequest instance
    # Pydantic validation errors produce a 422 response automatically
    return await self._service.create(body)
```

When `T` is not a Pydantic model, the raw body bytes are decoded as UTF-8 and passed to `T(decoded_string)`.

### Header[T] -- HTTP Headers

Extracts an HTTP header value. The parameter name is converted from `snake_case` to `kebab-case` for the header lookup:

```python
@get_mapping("/")
async def list_orders(self, x_api_key: Header[str]) -> dict:
    # Reads the "x-api-key" header (snake_case -> kebab-case)
    return await self._service.find_all_for_key(x_api_key)
```

- Missing headers return `None` if no default is set, or the default value.
- Supports type coercion just like other parameter types.

### Cookie[T] -- Cookies

Extracts a cookie value from the request:

```python
@get_mapping("/me")
async def get_current_user(self, session_id: Cookie[str]) -> dict:
    # Reads the "session_id" cookie
    return await self._service.get_by_session(session_id)
```

### Type Coercion

The `ParameterResolver` automatically coerces string values from the HTTP request to the annotated inner type `T`:

| Target Type | Conversion                          |
|-------------|-------------------------------------|
| `str`       | Passed through unchanged            |
| `int`       | `int(value)`                        |
| `float`     | `float(value)`                      |
| `bool`      | `bool(value)`                       |
| `UUID`      | `UUID(value)`                       |
| Any other   | `T(value)` -- calls the constructor |

The coercion is performed by the `_coerce()` method of `ParameterResolver`.

---

## Response Handling

### Return Value Conversion

PyFly automatically converts handler return values into HTTP responses using the `handle_return_value()` function:

| Return Value            | Response                                        |
|-------------------------|-------------------------------------------------|
| `None`                  | 204 No Content (unless `status_code` explicitly set) |
| `Response` (Starlette)  | Passed through unchanged                        |
| `BaseModel` (Pydantic)  | JSON via `model_dump(mode="json")`               |
| `dict`, `list`, `str`   | JSON response                                   |

Examples:

```python
@get_mapping("/{id}")
async def get_order(self, id: PathVar[str]) -> dict:
    return {"id": id, "status": "active"}       # -> 200 JSON

@delete_mapping("/{id}", status_code=204)
async def delete_order(self, id: PathVar[str]) -> None:
    await self._service.delete(id)               # -> 204 No Content

@get_mapping("/{id}")
async def get_order(self, id: PathVar[str]) -> OrderResponse:
    order = await self._service.find(id)
    return OrderResponse.model_validate(order)   # -> 200 JSON via model_dump
```

### handle_return_value()

The `handle_return_value(result, status_code=200)` function is the core of response conversion. It is called by the `ControllerRegistrar` after each handler invocation:

```python
from pyfly.web import handle_return_value

response = handle_return_value({"key": "value"}, status_code=200)
# -> JSONResponse({"key": "value"}, status_code=200)

response = handle_return_value(None)
# -> Response(status_code=204)

response = handle_return_value(None, status_code=200)
# -> Response(status_code=204) -- None always yields 204 unless explicitly overridden
```

---

## Exception Handling

PyFly provides a two-tier exception handling system: controller-level handlers for specific exceptions, and a global handler for everything else.

### Controller-Level Exception Handlers

Use the `@exception_handler` decorator to define methods that catch specific exceptions within a controller:

```python
from pyfly.kernel.exceptions import ResourceNotFoundException
from pyfly.web import exception_handler


@rest_controller
@request_mapping("/api/orders")
class OrderController:

    @get_mapping("/{order_id}")
    async def get_order(self, order_id: PathVar[str]) -> dict:
        order = await self._service.find_by_id(order_id)
        if not order:
            raise ResourceNotFoundException(f"Order {order_id} not found")
        return order

    @exception_handler(ResourceNotFoundException)
    async def handle_not_found(self, exc: ResourceNotFoundException):
        return 404, {"error": str(exc), "code": exc.code}

    @exception_handler(ValueError)
    async def handle_bad_input(self, exc: ValueError):
        return 400, {"error": str(exc)}
```

Exception handler methods can return:

- A `(status_code, body)` tuple -- converted to a `JSONResponse`
- A Starlette `Response` object -- passed through unchanged
- Any other value -- processed through `handle_return_value()`

When multiple exception handlers could match (e.g., both `Exception` and `ValueError`), handlers are sorted by MRO depth (most specific first), so subclass exceptions are matched before their parents.

### Global Exception Handler

Unhandled exceptions (those not caught by controller-level handlers) are caught by the global exception handler, which produces RFC 7807-style structured JSON error responses:

```json
{
  "error": {
    "message": "Order not found",
    "code": "ORDER_NOT_FOUND",
    "status": 404,
    "path": "/api/orders/abc-123",
    "timestamp": "2026-02-14T10:30:00+00:00",
    "transaction_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

For `PyFlyException` subclasses, the response includes the exception's `message`, `code`, and optional `context` dict. For unknown exceptions, the message is generalized to `"Internal server error"` with code `"INTERNAL_ERROR"` to avoid leaking internal details.

### Exception-to-Status Mapping

The global handler maps `PyFlyException` subclasses to HTTP status codes:

| Exception                     | HTTP Status |
|-------------------------------|-------------|
| `ValidationException`         | 422         |
| `ResourceNotFoundException`   | 404         |
| `ConflictException`           | 409         |
| `PreconditionFailedException` | 412         |
| `GoneException`               | 410         |
| `InvalidRequestException`     | 400         |
| `LockedResourceException`     | 423         |
| `MethodNotAllowedException`   | 405         |
| `UnsupportedMediaTypeException` | 415       |
| `PayloadTooLargeException`    | 413         |
| `UnauthorizedException`       | 401         |
| `ForbiddenException`          | 403         |
| `SecurityException`           | 401         |
| `QuotaExceededException`      | 429         |
| `RateLimitException`          | 429         |
| `CircuitBreakerException`     | 503         |
| `BulkheadException`           | 503         |
| `ServiceUnavailableException` | 503         |
| `DegradedServiceException`    | 503         |
| `OperationTimeoutException`   | 504         |
| `NotImplementedException`     | 501         |
| `BadGatewayException`         | 502         |
| `GatewayTimeoutException`     | 504         |
| `BusinessException` (catch-all) | 400       |
| `InfrastructureException` (catch-all) | 502 |
| Unknown exceptions            | 500         |

### Exception Converters

PyFly includes a chain-of-responsibility exception converter system (`pyfly.web.converters`) that translates common library exceptions into PyFly exceptions before the global handler processes them:

| Library Exception           | PyFly Exception           |
|-----------------------------|---------------------------|
| `pydantic.ValidationError`  | `ValidationException`     |
| `json.JSONDecodeError`      | `InvalidRequestException` |

You can register custom converters by implementing the `ExceptionConverter` protocol:

```python
from pyfly.web.converters import ExceptionConverter
from pyfly.kernel.exceptions import PyFlyException, BusinessException


class MyLibraryExceptionConverter:
    def can_handle(self, exc: Exception) -> bool:
        return isinstance(exc, MyLibraryError)

    def convert(self, exc: Exception) -> PyFlyException:
        return BusinessException(str(exc), code="MY_LIB_ERROR")
```

---

## Middleware

PyFly's `create_app()` factory automatically includes built-in middleware. Additional middleware can be added manually.

### TransactionIdMiddleware

Automatically included in every PyFly application. Ensures every request/response pair carries a unique transaction ID for distributed tracing.

**Behavior:**
1. Checks for an incoming `X-Transaction-Id` header.
2. If present, propagates it. If absent, generates a new UUID.
3. Stores the ID on `request.state.transaction_id`.
4. Adds the `X-Transaction-Id` header to the response.

```
Request  -> X-Transaction-Id: abc-123    -> propagated
Request  -> (no header)                  -> X-Transaction-Id: <generated-uuid>
Response -> X-Transaction-Id: abc-123
```

### RequestLoggingMiddleware

Automatically included. Logs every HTTP request with structured fields using `structlog`:

- HTTP method
- Request path
- Response status code
- Duration in milliseconds
- Transaction ID

Sample structured log output:

```
event=http_request method=GET path=/api/orders status_code=200 duration_ms=12.34 transaction_id=abc-123
```

Failed requests are logged at the `error` level with the exception type and message.

### SecurityHeadersMiddleware

Adds OWASP-recommended security headers to every response. Configure it with a `SecurityHeadersConfig`:

```python
from starlette.middleware import Middleware
from pyfly.web import SecurityHeadersMiddleware, SecurityHeadersConfig

config = SecurityHeadersConfig(
    x_content_type_options="nosniff",
    x_frame_options="DENY",
    strict_transport_security="max-age=31536000; includeSubDomains",
    x_xss_protection="0",
    referrer_policy="strict-origin-when-cross-origin",
    content_security_policy="default-src 'self'",
    permissions_policy="geolocation=()",
)

# Add to Starlette manually
app.add_middleware(SecurityHeadersMiddleware, config=config)
```

If no config is provided, OWASP defaults are used automatically.

### Custom Middleware

You can add any Starlette-compatible middleware via `extra_routes` or by modifying the Starlette app directly after `create_app()`:

```python
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Your rate limiting logic
        return await call_next(request)


app = create_app(context=ctx)
app.add_middleware(RateLimitMiddleware)
```

---

## CORS Configuration

Configure Cross-Origin Resource Sharing with the `CORSConfig` dataclass:

```python
from pyfly.web import CORSConfig

cors = CORSConfig(
    allowed_origins=["https://myapp.com", "http://localhost:3000"],
    allowed_methods=["GET", "POST", "PUT", "DELETE"],
    allowed_headers=["*"],
    allow_credentials=True,
    exposed_headers=["X-Transaction-Id"],
    max_age=3600,
)

app = create_app(title="My API", context=ctx, cors=cors)
```

| Field               | Type         | Default   | Description                            |
|---------------------|--------------|-----------|----------------------------------------|
| `allowed_origins`   | `list[str]`  | `["*"]`   | Origins permitted to access the API    |
| `allowed_methods`   | `list[str]`  | `["GET"]` | HTTP methods allowed in CORS requests  |
| `allowed_headers`   | `list[str]`  | `["*"]`   | Request headers allowed in CORS        |
| `allow_credentials` | `bool`       | `False`   | Allow cookies and auth headers         |
| `exposed_headers`   | `list[str]`  | `[]`      | Response headers visible to the browser|
| `max_age`           | `int`        | `600`     | Preflight cache duration in seconds    |

`CORSConfig` is a frozen dataclass. When passed to `create_app()`, it is translated into Starlette's built-in `CORSMiddleware`.

---

## Security Headers

The `SecurityHeadersConfig` dataclass controls which security headers are added to every response:

```python
from pyfly.web import SecurityHeadersConfig

config = SecurityHeadersConfig(
    x_content_type_options="nosniff",                              # Prevent MIME sniffing
    x_frame_options="DENY",                                        # Prevent clickjacking
    strict_transport_security="max-age=31536000; includeSubDomains",  # HSTS
    x_xss_protection="0",                                          # Disable legacy XSS auditor
    referrer_policy="strict-origin-when-cross-origin",             # Control Referer
    content_security_policy="default-src 'self'",                  # CSP (None = omit)
    permissions_policy="geolocation=()",                           # Permissions (None = omit)
)
```

| Header                        | Config Field                   | Default                                    |
|-------------------------------|--------------------------------|--------------------------------------------|
| `X-Content-Type-Options`      | `x_content_type_options`       | `"nosniff"`                                |
| `X-Frame-Options`             | `x_frame_options`              | `"DENY"`                                   |
| `Strict-Transport-Security`   | `strict_transport_security`    | `"max-age=31536000; includeSubDomains"`    |
| `X-XSS-Protection`            | `x_xss_protection`             | `"0"` (modern recommendation)              |
| `Referrer-Policy`             | `referrer_policy`              | `"strict-origin-when-cross-origin"`        |
| `Content-Security-Policy`     | `content_security_policy`      | `None` (too app-specific; omitted)         |
| `Permissions-Policy`          | `permissions_policy`           | `None` (too app-specific; omitted)         |

---

## OpenAPI and Swagger Documentation

### Automatic Generation

When `docs_enabled=True` (the default), `create_app()` generates a complete OpenAPI 3.1 specification from controller metadata and mounts three documentation endpoints.

### Swagger UI

Available at `/docs`. Provides an interactive API explorer where you can try out requests directly:

```
http://localhost:8080/docs
```

### ReDoc

Available at `/redoc`. Provides a clean, readable API reference:

```
http://localhost:8080/redoc
```

### OpenAPI JSON

The raw OpenAPI 3.1 specification is served at `/openapi.json`.

### OpenAPIGenerator Internals

The `OpenAPIGenerator` class (`pyfly.web.openapi`) builds the spec:

1. **Info** -- populated from `title`, `version`, and `description` passed to `create_app()`.
2. **Paths** -- built from `RouteMetadata` collected by `ControllerRegistrar.collect_route_metadata()`. Each handler contributes an operation with `operationId`, parameters, request body, and responses.
3. **Components/Schemas** -- Pydantic models used as `Body[T]` types are registered in `components.schemas` via `model_json_schema()`, and referenced using `$ref`.

Parameters are extracted from handler type hints:
- `PathVar[T]` becomes an `in: path` parameter
- `QueryParam[T]` becomes an `in: query` parameter
- `Header[T]` becomes an `in: header` parameter
- `Cookie[T]` becomes an `in: cookie` parameter
- `Body[BaseModel]` becomes a `requestBody` with a JSON schema reference

---

## Application Factory: create_app()

The `create_app()` function is the primary entry point for building a PyFly web application:

```python
from pyfly.web import create_app, CORSConfig

app = create_app(
    title="Order Service",
    version="1.0.0",
    description="REST API for order management",
    debug=False,
    context=application_context,
    docs_enabled=True,
    actuator_enabled=True,
    cors=CORSConfig(allowed_origins=["*"], allowed_methods=["GET", "POST"]),
    extra_routes=[],
)
```

### Full Parameter Reference

| Parameter          | Type                         | Default    | Description                                               |
|--------------------|------------------------------|------------|-----------------------------------------------------------|
| `title`            | `str`                        | `"PyFly"`  | API title for OpenAPI spec                                |
| `version`          | `str`                        | `"0.1.0"`  | API version for OpenAPI spec                              |
| `description`      | `str`                        | `""`       | API description for OpenAPI spec                          |
| `debug`            | `bool`                       | `False`    | Starlette debug mode                                      |
| `context`          | `ApplicationContext \| None` | `None`     | DI context for auto-discovering `@rest_controller` beans  |
| `docs_enabled`     | `bool`                       | `True`     | Mount OpenAPI spec, Swagger UI, and ReDoc                 |
| `extra_routes`     | `list[Route] \| None`        | `None`     | Additional Starlette routes to mount                      |
| `actuator_enabled` | `bool`                       | `False`    | Mount actuator health/info endpoints                      |
| `cors`             | `CORSConfig \| None`         | `None`     | CORS configuration (None = no CORS middleware)             |

### What create_app() Does

1. Creates a middleware stack with `TransactionIdMiddleware` and `RequestLoggingMiddleware`.
2. Adds `CORSMiddleware` if a `CORSConfig` is provided.
3. Uses `ControllerRegistrar.collect_routes(context)` to discover all `@rest_controller` beans and build Starlette `Route` objects.
4. Appends any `extra_routes`.
5. Mounts actuator endpoints if `actuator_enabled=True`.
6. Generates OpenAPI spec and mounts `/openapi.json`, `/docs`, and `/redoc` if `docs_enabled=True`.
7. Builds the Starlette `Application` and registers the `global_exception_handler`.
8. Returns the fully configured `Starlette` application instance, ready to be served by Uvicorn or any ASGI server.

---

## ControllerRegistrar

The `ControllerRegistrar` is the bridge between PyFly's decorator-based controller definitions and Starlette's routing system.

### Route Collection

`collect_routes(context)` iterates over all beans in the `ApplicationContext` and, for each class with `__pyfly_stereotype__ == "rest_controller"`:

1. Reads the `__pyfly_request_mapping__` base path from the class.
2. Iterates over all methods to find those with a `__pyfly_mapping__` attribute.
3. Combines the base path with each method's relative path.
4. Creates a `ParameterResolver` for each handler.
5. Collects `@exception_handler` methods for the controller.
6. Wraps each handler in an async endpoint that resolves parameters, calls the handler, converts the return value, and dispatches exceptions to the appropriate handler.
7. Returns a list of Starlette `Route` objects.

### Route Metadata for OpenAPI

`collect_route_metadata(context)` performs the same discovery but returns `RouteMetadata` objects instead of `Route` objects. Each `RouteMetadata` contains:

- `path`, `http_method`, `status_code`
- `handler`, `handler_name`
- `parameters` -- list of OpenAPI parameter dicts extracted from type hints
- `request_body_model` -- the Pydantic model class if `Body[BaseModel]` is used
- `return_type` -- the handler's return type annotation

This metadata is consumed by `OpenAPIGenerator` to build the spec.

### Exception Handler Discovery

`_collect_exception_handlers(instance)` scans a controller instance for methods decorated with `@exception_handler`. Handlers are sorted by MRO depth (most specific first) so that `ValueError` is matched before `Exception`, for instance.

---

## ParameterResolver

The `ParameterResolver` (`pyfly.web.adapters.starlette.resolver`) is responsible for turning a Starlette `Request` into a dict of keyword arguments for a handler method.

**At startup** (`__init__`): Inspects the handler's type hints and builds a list of `ResolvedParam` objects, each containing:
- `name` -- the parameter name
- `binding_type` -- `PathVar`, `QueryParam`, `Body`, `Header`, or `Cookie`
- `inner_type` -- the type argument `T` (e.g., `str`, `int`, a Pydantic model)
- `default` -- the default value if provided in the signature

**At request time** (`resolve(request)`): For each `ResolvedParam`, calls the appropriate private resolver method (`_resolve_path_var`, `_resolve_query_param`, `_resolve_body`, `_resolve_header`, `_resolve_cookie`) and returns the assembled kwargs dict.

---

## WebServerPort

The `WebServerPort` protocol (`pyfly.web.ports.outbound`) defines the contract for any web server adapter:

```python
@runtime_checkable
class WebServerPort(Protocol):
    def create_app(self, **kwargs: Any) -> Any:
        """Create and return a web application instance."""
        ...
```

This protocol ensures that the application layer never depends directly on Starlette. In theory, you could implement a Flask adapter, a Django adapter, or any other ASGI/WSGI adapter by implementing this port.

---

## Complete CRUD Example

The following example demonstrates a full CRUD controller with all HTTP methods, Pydantic validation, exception handling, and proper status codes.

```python
from uuid import UUID
from pydantic import BaseModel, Field

from pyfly.container import rest_controller, service
from pyfly.kernel.exceptions import ResourceNotFoundException
from pyfly.web import (
    request_mapping, get_mapping, post_mapping, put_mapping, patch_mapping,
    delete_mapping, exception_handler, Body, PathVar, QueryParam,
)


# --- Request/Response Models ---

class CreateProductRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price: float = Field(..., gt=0)
    category: str

class UpdateProductRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price: float = Field(..., gt=0)
    category: str

class PatchProductRequest(BaseModel):
    name: str | None = None
    price: float | None = Field(None, gt=0)
    category: str | None = None

class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    category: str


# --- Service Layer ---

@service
class ProductService:
    async def find_all(self, category: str | None = None) -> list[dict]:
        # Business logic here
        ...

    async def find_by_id(self, product_id: str) -> dict:
        # Raises ResourceNotFoundException if not found
        ...

    async def create(self, data: CreateProductRequest) -> dict:
        ...

    async def replace(self, product_id: str, data: UpdateProductRequest) -> dict:
        ...

    async def patch(self, product_id: str, data: PatchProductRequest) -> dict:
        ...

    async def delete(self, product_id: str) -> None:
        ...


# --- Controller ---

@rest_controller
@request_mapping("/api/products")
class ProductController:

    def __init__(self, product_service: ProductService) -> None:
        self._service = product_service

    # LIST all products with optional category filter
    @get_mapping("/")
    async def list_products(
        self,
        category: QueryParam[str] = None,
        page: QueryParam[int] = 1,
        size: QueryParam[int] = 20,
    ) -> list[dict]:
        return await self._service.find_all(category=category)

    # GET a single product by ID
    @get_mapping("/{product_id}")
    async def get_product(self, product_id: PathVar[str]) -> dict:
        return await self._service.find_by_id(product_id)

    # CREATE a new product (201 Created)
    @post_mapping("/", status_code=201)
    async def create_product(self, body: Body[CreateProductRequest]) -> dict:
        return await self._service.create(body)

    # REPLACE a product (full update)
    @put_mapping("/{product_id}")
    async def replace_product(
        self,
        product_id: PathVar[str],
        body: Body[UpdateProductRequest],
    ) -> dict:
        return await self._service.replace(product_id, body)

    # PATCH a product (partial update)
    @patch_mapping("/{product_id}")
    async def update_product(
        self,
        product_id: PathVar[str],
        body: Body[PatchProductRequest],
    ) -> dict:
        return await self._service.patch(product_id, body)

    # DELETE a product (204 No Content)
    @delete_mapping("/{product_id}", status_code=204)
    async def delete_product(self, product_id: PathVar[str]) -> None:
        await self._service.delete(product_id)

    # --- Exception Handlers ---

    @exception_handler(ResourceNotFoundException)
    async def handle_not_found(self, exc: ResourceNotFoundException):
        return 404, {
            "error": {
                "message": str(exc),
                "code": exc.code or "NOT_FOUND",
            }
        }

    @exception_handler(ValueError)
    async def handle_value_error(self, exc: ValueError):
        return 400, {
            "error": {
                "message": str(exc),
                "code": "BAD_REQUEST",
            }
        }
```

**Running the application:**

```python
from pyfly.web import create_app, CORSConfig

app = create_app(
    title="Product Service",
    version="1.0.0",
    description="CRUD API for product management",
    context=application_context,
    docs_enabled=True,
    cors=CORSConfig(
        allowed_origins=["http://localhost:3000"],
        allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    ),
)

# Run with: uvicorn main:app --reload
```

This will expose:
- `GET    /api/products/`             -- list products
- `GET    /api/products/{product_id}` -- get a product
- `POST   /api/products/`             -- create a product
- `PUT    /api/products/{product_id}` -- replace a product
- `PATCH  /api/products/{product_id}` -- partially update a product
- `DELETE /api/products/{product_id}` -- delete a product
- `GET    /docs`                       -- Swagger UI
- `GET    /redoc`                      -- ReDoc
- `GET    /openapi.json`               -- OpenAPI 3.1 spec
