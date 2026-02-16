# HTTPX Adapter

> **Module:** Client — [Module Guide](../modules/client.md)
> **Package:** `pyfly.client.adapters.httpx_adapter`
> **Backend:** HTTPX 0.27+

## Quick Start

### Installation

```bash
pip install pyfly[client]
```

### Minimal Configuration

```yaml
# pyfly.yaml
pyfly:
  client:
    timeout: 30
```

### Minimal Example

```python
from pyfly.client import http_client, get


@http_client(base_url="http://order-service:8080")
class OrderClient:
    @get("/api/orders")
    async def list_orders(self) -> list:
        ...
```

---

## Configuration Reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `pyfly.client.timeout` | `int` | `30` | Request timeout in seconds |
| `pyfly.client.retry.max-attempts` | `int` | `3` | Maximum retry attempts |
| `pyfly.client.retry.base-delay` | `float` | `1.0` | Base delay for exponential backoff (seconds) |
| `pyfly.client.circuit-breaker.failure-threshold` | `int` | `5` | Failures before opening the circuit |
| `pyfly.client.circuit-breaker.recovery-timeout` | `int` | `30` | Seconds before attempting recovery |

---

## Adapter-Specific Features

### HttpxClientAdapter

Implements `HttpClientPort` using `httpx.AsyncClient`.

- **Constructor params:** `base_url`, `timeout` (timedelta), `headers` (dict)
- **Returns:** Raw `httpx.Response` objects for full control
- **Lifecycle:** Clean shutdown via `aclose()` in `stop()`

### Resilience Integration

The client module integrates with PyFly's resilience patterns:

- **Circuit Breaker** — Stops calling a failing service after a threshold
- **Retry** — Retries failed requests with exponential backoff
- **Timeout** — Enforces request deadlines

---

## Testing

Mock the `HttpClientPort` in tests — no real HTTP calls needed:

```python
from unittest.mock import AsyncMock

mock_client = AsyncMock(spec=HttpClientPort)
mock_client.request.return_value = mock_response
```

---

## See Also

- [Client Module Guide](../modules/client.md) — Full API reference: declarative `@http_client`, circuit breaker, retry
- [Resilience Module Guide](../modules/resilience.md) — Rate limiting, bulkhead, timeout, fallback patterns
- [Adapter Catalog](README.md)
