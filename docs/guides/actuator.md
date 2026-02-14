# Actuator Guide

The actuator module provides production-ready monitoring and management endpoints
for PyFly applications. Inspired by Spring Boot Actuator, it exposes HTTP endpoints
that reveal the health, configuration, and composition of your running application.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Enabling Actuator](#enabling-actuator)
   - [Via create_app()](#via-create_app)
   - [Via pyfly.yaml](#via-pyflyyaml)
3. [Health Endpoint](#health-endpoint)
   - [Response Format](#response-format)
   - [HTTP Status Codes](#http-status-codes)
4. [HealthIndicator Protocol](#healthindicator-protocol)
5. [HealthStatus Dataclass](#healthstatus-dataclass)
6. [HealthAggregator](#healthaggregator)
   - [add_indicator()](#add_indicator)
   - [check()](#check)
   - [Aggregation Rules](#aggregation-rules)
7. [HealthResult Dataclass](#healthresult-dataclass)
8. [Custom Health Indicators](#custom-health-indicators)
   - [Database Health Indicator](#database-health-indicator)
   - [Redis Health Indicator](#redis-health-indicator)
   - [External Service Health Indicator](#external-service-health-indicator)
9. [Beans Endpoint](#beans-endpoint)
10. [Environment Endpoint](#environment-endpoint)
11. [Info Endpoint](#info-endpoint)
12. [make_actuator_routes()](#make_actuator_routes)
13. [Configuration](#configuration)
14. [Complete Example](#complete-example)

---

## Introduction

In production, operators need answers to questions like:

- "Is this service healthy enough to receive traffic?"
- "What beans are registered in the application context?"
- "What configuration profile is active?"
- "What version of the service is running?"

The actuator module answers all of these through standard HTTP GET endpoints:

| Endpoint              | Description                     |
|-----------------------|---------------------------------|
| `GET /actuator/health` | Application health status       |
| `GET /actuator/beans`  | Registered bean information     |
| `GET /actuator/env`    | Active profiles                 |
| `GET /actuator/info`   | Application metadata            |

```python
from pyfly.actuator import (
    HealthIndicator, HealthStatus, HealthResult,
    HealthAggregator, make_actuator_routes,
)
```

**Source:** `src/pyfly/actuator/__init__.py`

---

## Enabling Actuator

### Via create_app()

Pass `actuator_enabled=True` when creating the web application:

```python
from pyfly.web import create_app

app = create_app(
    title="Order Service",
    version="1.0.0",
    context=application_context,
    actuator_enabled=True,
)
```

When actuator is enabled with a `context`, the framework automatically:

1. Creates a `HealthAggregator` instance.
2. Scans the DI container for any beans that implement the `HealthIndicator`
   protocol.
3. Registers each discovered health indicator with the aggregator.
4. Mounts the `/actuator/health`, `/actuator/beans`, `/actuator/env`, and
   `/actuator/info` routes.

### Via pyfly.yaml

Set the actuator enabled flag in your configuration file:

```yaml
pyfly:
  web:
    actuator:
      enabled: true
```

The framework default (from `pyfly-defaults.yaml`) is `enabled: false`.

---

## Health Endpoint

**Endpoint:** `GET /actuator/health`

The health endpoint runs all registered health indicators and returns an aggregated
health result.

### Response Format

When all components are healthy:

```json
{
    "status": "UP",
    "components": {
        "database": {
            "status": "UP",
            "details": {
                "type": "postgresql",
                "version": "16.1"
            }
        },
        "redis": {
            "status": "UP",
            "details": {
                "cluster_mode": false
            }
        }
    }
}
```

When one or more components are unhealthy:

```json
{
    "status": "DOWN",
    "components": {
        "database": {
            "status": "UP",
            "details": {"type": "postgresql"}
        },
        "redis": {
            "status": "DOWN",
            "details": {"error": "Connection refused"}
        }
    }
}
```

When no health indicators are registered:

```json
{
    "status": "UP"
}
```

### HTTP Status Codes

| Overall Status | HTTP Code | Meaning                                    |
|----------------|-----------|---------------------------------------------|
| `"UP"`         | `200 OK`  | All components are healthy                  |
| `"DOWN"`       | `503 Service Unavailable` | One or more components are unhealthy |

This mapping is implemented in `get_health_data()`:

```python
async def get_health_data(health_aggregator: HealthAggregator) -> tuple[dict, int]:
    result = await health_aggregator.check()
    status_code = 200 if result.status != "DOWN" else 503
    return result.to_dict(), status_code
```

**Source:** `src/pyfly/actuator/endpoints.py`

---

## HealthIndicator Protocol

`HealthIndicator` is a runtime-checkable Protocol that any bean can implement to
contribute health information to the actuator.

```python
from pyfly.actuator import HealthIndicator, HealthStatus

@runtime_checkable
class HealthIndicator(Protocol):
    async def health(self) -> HealthStatus: ...
```

Any class with an `async def health(self) -> HealthStatus` method satisfies this
protocol. When actuator is enabled, the framework scans for beans implementing this
protocol and automatically registers them as health indicators.

**Source:** `src/pyfly/actuator/health.py`

---

## HealthStatus Dataclass

`HealthStatus` represents the health of a single component.

```python
from pyfly.actuator import HealthStatus

@dataclass
class HealthStatus:
    status: str                            # "UP", "DOWN", or "DEGRADED"
    details: dict[str, Any] = field(default_factory=dict)
```

| Field     | Type              | Description                                   |
|-----------|-------------------|-----------------------------------------------|
| `status`  | `str`             | Health state: `"UP"`, `"DOWN"`, or `"DEGRADED"` |
| `details` | `dict[str, Any]`  | Additional information (version, type, error, etc.) |

**Usage:**

```python
# Healthy component
HealthStatus(status="UP", details={"type": "postgresql", "version": "16.1"})

# Unhealthy component
HealthStatus(status="DOWN", details={"error": "Connection timed out"})

# Degraded component
HealthStatus(status="DEGRADED", details={"active_connections": 95, "max": 100})
```

---

## HealthAggregator

`HealthAggregator` collects health indicators from multiple components and produces
an aggregated `HealthResult`.

```python
from pyfly.actuator import HealthAggregator

aggregator = HealthAggregator()
```

### add_indicator()

Register a named health indicator:

```python
aggregator.add_indicator("database", DatabaseHealthIndicator())
aggregator.add_indicator("redis", RedisHealthIndicator())
aggregator.add_indicator("payment-gateway", PaymentGatewayHealthIndicator())
```

**Parameters:**

| Parameter   | Type              | Description                        |
|-------------|-------------------|------------------------------------|
| `name`      | `str`             | Unique name for this indicator     |
| `indicator` | `HealthIndicator` | Object implementing the protocol   |

### check()

Run all registered health indicators and return an aggregated result:

```python
result = await aggregator.check()
print(result.status)      # "UP" or "DOWN"
print(result.components)  # {"database": HealthStatus(...), "redis": HealthStatus(...)}
```

**Returns:** A `HealthResult` dataclass.

### Aggregation Rules

The aggregator follows these rules:

1. **All UP:** If every indicator reports `"UP"`, the overall status is `"UP"`.
2. **Any DOWN:** If any indicator reports `"DOWN"`, the overall status is `"DOWN"`.
3. **Exception:** If an indicator's `health()` method raises an exception, that
   indicator is treated as `"DOWN"` with `details={"error": "check failed"}`.
   The exception is logged but does not crash the health check.
4. **No indicators:** If no indicators are registered, the overall status is `"UP"`.

```python
if not self._indicators:
    return HealthResult(status="UP")

for name, indicator in self._indicators.items():
    try:
        status = await indicator.health()
        components[name] = status
        if status.status == "DOWN":
            overall = "DOWN"
    except Exception:
        logger.exception("Health indicator '%s' raised an exception", name)
        components[name] = HealthStatus(status="DOWN", details={"error": "check failed"})
        overall = "DOWN"
```

**Source:** `src/pyfly/actuator/health.py`

---

## HealthResult Dataclass

`HealthResult` is the aggregated result returned by `HealthAggregator.check()`.

```python
from pyfly.actuator import HealthResult

@dataclass
class HealthResult:
    status: str
    components: dict[str, HealthStatus] = field(default_factory=dict)
```

| Field        | Type                          | Description                           |
|-------------|-------------------------------|---------------------------------------|
| `status`    | `str`                         | Overall status: `"UP"` or `"DOWN"`    |
| `components` | `dict[str, HealthStatus]`    | Per-component health status           |

### to_dict()

Serializes the result to a JSON-friendly dictionary:

```python
result = HealthResult(
    status="UP",
    components={
        "database": HealthStatus(status="UP", details={"type": "postgresql"}),
        "redis": HealthStatus(status="UP"),
    },
)

result.to_dict()
# {
#     "status": "UP",
#     "components": {
#         "database": {"status": "UP", "details": {"type": "postgresql"}},
#         "redis": {"status": "UP", "details": {}}
#     }
# }
```

If there are no components, the `"components"` key is omitted:

```python
HealthResult(status="UP").to_dict()
# {"status": "UP"}
```

---

## Custom Health Indicators

### Database Health Indicator

```python
from pyfly.actuator import HealthIndicator, HealthStatus
from pyfly.container import component


@component
class DatabaseHealthIndicator:
    """Checks database connectivity by executing a lightweight query."""

    def __init__(self, db_session_factory) -> None:
        self._session_factory = db_session_factory

    async def health(self) -> HealthStatus:
        try:
            async with self._session_factory() as session:
                await session.execute("SELECT 1")
            return HealthStatus(
                status="UP",
                details={
                    "type": "postgresql",
                    "version": "16.1",
                },
            )
        except Exception as e:
            return HealthStatus(
                status="DOWN",
                details={"error": str(e)},
            )
```

### Redis Health Indicator

```python
@component
class RedisHealthIndicator:
    """Checks Redis connectivity with a PING command."""

    def __init__(self, redis_client) -> None:
        self._redis = redis_client

    async def health(self) -> HealthStatus:
        try:
            await self._redis.ping()
            info = await self._redis.info("server")
            return HealthStatus(
                status="UP",
                details={
                    "version": info.get("redis_version", "unknown"),
                    "cluster_mode": info.get("cluster_enabled", "0") == "1",
                },
            )
        except Exception as e:
            return HealthStatus(
                status="DOWN",
                details={"error": str(e)},
            )
```

### External Service Health Indicator

```python
import httpx


@component
class PaymentGatewayHealthIndicator:
    """Checks connectivity to an external payment gateway."""

    async def health(self) -> HealthStatus:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("https://api.payment-gateway.com/health")
                if response.status_code == 200:
                    return HealthStatus(
                        status="UP",
                        details={"response_time_ms": response.elapsed.total_seconds() * 1000},
                    )
                return HealthStatus(
                    status="DOWN",
                    details={"http_status": response.status_code},
                )
        except httpx.RequestError as e:
            return HealthStatus(
                status="DOWN",
                details={"error": str(e)},
            )
```

Because these classes are decorated with `@component`, they are automatically
discovered during package scanning. Because they implement the `HealthIndicator`
protocol (they have `async def health() -> HealthStatus`), the actuator
automatically registers them as indicators.

---

## Beans Endpoint

**Endpoint:** `GET /actuator/beans`

Returns information about all beans registered in the DI container.

**Response format:**

```json
{
    "beans": {
        "OrderService": {
            "type": "order_service.services.OrderService",
            "scope": "SINGLETON",
            "stereotype": "service"
        },
        "OrderRepository": {
            "type": "order_service.repositories.OrderRepository",
            "scope": "SINGLETON",
            "stereotype": "repository"
        },
        "OrderController": {
            "type": "order_service.controllers.OrderController",
            "scope": "SINGLETON",
            "stereotype": "rest_controller"
        }
    }
}
```

Each bean entry contains:

| Field        | Description                                           |
|-------------|-------------------------------------------------------|
| `type`      | Fully qualified class name (`module.ClassName`)        |
| `scope`     | Lifecycle scope: `SINGLETON`, `TRANSIENT`, or `REQUEST` |
| `stereotype` | Stereotype: `component`, `service`, `repository`, `controller`, `rest_controller`, `configuration`, or `none` |

The data is produced by `get_beans_data()`, which iterates over the container's
registration dictionary.

**Source:** `src/pyfly/actuator/endpoints.py`

---

## Environment Endpoint

**Endpoint:** `GET /actuator/env`

Returns the active configuration profiles.

**Response format:**

```json
{
    "activeProfiles": ["dev", "local"]
}
```

If no profiles are active:

```json
{
    "activeProfiles": []
}
```

Profiles are set via `pyfly.yaml` or the `PYFLY_PROFILES_ACTIVE` environment
variable:

```yaml
pyfly:
  profiles:
    active: dev,local
```

```bash
export PYFLY_PROFILES_ACTIVE=production
```

---

## Info Endpoint

**Endpoint:** `GET /actuator/info`

Returns application metadata from the configuration.

**Response format:**

```json
{
    "app": {
        "name": "order-service",
        "version": "1.0.0",
        "description": "Order management microservice"
    }
}
```

The values come from the `pyfly.app` configuration section:

```yaml
pyfly:
  app:
    name: order-service
    version: 1.0.0
    description: Order management microservice
```

---

## make_actuator_routes()

`make_actuator_routes()` builds the HTTP route objects for the actuator endpoints.
It is called internally by `create_app()` when `actuator_enabled=True`, but you can
also call it directly for advanced use cases.

```python
from pyfly.actuator import make_actuator_routes, HealthAggregator

aggregator = HealthAggregator()
aggregator.add_indicator("database", DatabaseHealthIndicator())

routes = make_actuator_routes(
    health_aggregator=aggregator,
    context=application_context,  # Optional: enables beans/env/info endpoints
)
```

**Parameters:**

| Parameter            | Type                           | Default | Description                  |
|---------------------|--------------------------------|---------|------------------------------|
| `health_aggregator` | `HealthAggregator`             | required | The aggregator for health checks |
| `context`           | `ApplicationContext \| None`   | `None`  | Application context (enables beans/env/info) |

**Behavior:**

- The `/actuator/health` endpoint is always created.
- The `/actuator/beans`, `/actuator/env`, and `/actuator/info` endpoints are only
  created when `context` is provided.

Internally, `make_actuator_routes()` delegates to the Starlette adapter which creates
`starlette.routing.Route` objects.

**Source:** `src/pyfly/actuator/endpoints.py`, `src/pyfly/actuator/adapters/starlette.py`

---

## Configuration

Actuator-related settings in `pyfly.yaml`:

```yaml
pyfly:
  app:
    name: order-service               # Shown in /actuator/info
    version: 1.0.0                     # Shown in /actuator/info
    description: Order management API  # Shown in /actuator/info

  profiles:
    active: production                 # Shown in /actuator/env

  web:
    actuator:
      enabled: true                    # Enable/disable actuator endpoints
```

The framework defaults (from `pyfly-defaults.yaml`):

```yaml
pyfly:
  app:
    name: "pyfly-app"
    version: "0.1.0"
    description: ""
  web:
    actuator:
      enabled: false
```

---

## Complete Example

The following example shows a full application with custom health indicators for a
database and an external payment service.

```python
"""order_service/app.py"""

from pyfly.core import pyfly_application, PyFlyApplication
from pyfly.container import component, service, rest_controller
from pyfly.web import create_app, request_mapping, get_mapping
from pyfly.actuator import HealthStatus


# =========================================================================
# Custom Health Indicators
# =========================================================================

@component
class DatabaseHealthIndicator:
    """Contributes database health to /actuator/health."""

    async def health(self) -> HealthStatus:
        try:
            # Replace with actual database connectivity check
            # await db.execute("SELECT 1")
            return HealthStatus(
                status="UP",
                details={
                    "type": "postgresql",
                    "version": "16.1",
                    "pool_active": 3,
                    "pool_max": 20,
                },
            )
        except Exception as e:
            return HealthStatus(
                status="DOWN",
                details={"error": str(e)},
            )


@component
class PaymentServiceHealthIndicator:
    """Contributes payment service health to /actuator/health."""

    async def health(self) -> HealthStatus:
        try:
            # Replace with actual HTTP health check
            # response = await httpx.get("https://payments.example.com/health")
            return HealthStatus(
                status="UP",
                details={"provider": "stripe", "response_time_ms": 45},
            )
        except Exception as e:
            return HealthStatus(
                status="DOWN",
                details={"error": str(e)},
            )


# =========================================================================
# Service and Controller
# =========================================================================

@service
class OrderService:
    async def list_orders(self) -> list[dict]:
        return [
            {"id": "ord-001", "status": "shipped"},
            {"id": "ord-002", "status": "processing"},
        ]


@rest_controller
@request_mapping("/api/orders")
class OrderController:
    def __init__(self, order_service: OrderService) -> None:
        self._service = order_service

    @get_mapping("")
    async def list_orders(self) -> list[dict]:
        return await self._service.list_orders()


# =========================================================================
# Application
# =========================================================================

@pyfly_application(
    name="order-service",
    version="1.0.0",
    scan_packages=["order_service"],
    description="Order management microservice",
)
class Application:
    pass


async def main():
    pyfly_app = PyFlyApplication(Application)
    await pyfly_app.startup()

    app = create_app(
        title="Order Service",
        version="1.0.0",
        context=pyfly_app.context,
        actuator_enabled=True,  # Enables all actuator endpoints
    )

    # The following endpoints are now available:
    # GET /actuator/health  -- aggregated health from both indicators
    # GET /actuator/beans   -- all registered beans
    # GET /actuator/env     -- active profiles
    # GET /actuator/info    -- app name, version, description

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

**Testing the actuator endpoints with `curl`:**

```bash
# Health check
curl http://localhost:8080/actuator/health
# {
#   "status": "UP",
#   "components": {
#     "DatabaseHealthIndicator": {
#       "status": "UP",
#       "details": {"type": "postgresql", "version": "16.1", ...}
#     },
#     "PaymentServiceHealthIndicator": {
#       "status": "UP",
#       "details": {"provider": "stripe", "response_time_ms": 45}
#     }
#   }
# }

# Bean registry
curl http://localhost:8080/actuator/beans
# {
#   "beans": {
#     "DatabaseHealthIndicator": {"type": "...", "scope": "SINGLETON", "stereotype": "component"},
#     "PaymentServiceHealthIndicator": {"type": "...", "scope": "SINGLETON", "stereotype": "component"},
#     "OrderService": {"type": "...", "scope": "SINGLETON", "stereotype": "service"},
#     "OrderController": {"type": "...", "scope": "SINGLETON", "stereotype": "rest_controller"}
#   }
# }

# Environment
curl http://localhost:8080/actuator/env
# {"activeProfiles": ["production"]}

# Application info
curl http://localhost:8080/actuator/info
# {"app": {"name": "order-service", "version": "1.0.0", "description": "Order management microservice"}}
```

**Kubernetes liveness and readiness probes:**

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: order-service
      image: order-service:1.0.0
      livenessProbe:
        httpGet:
          path: /actuator/health
          port: 8080
        initialDelaySeconds: 10
        periodSeconds: 30
      readinessProbe:
        httpGet:
          path: /actuator/health
          port: 8080
        initialDelaySeconds: 5
        periodSeconds: 10
```
