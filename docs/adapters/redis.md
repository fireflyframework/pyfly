# Redis Adapter

> **Module:** Caching — [Module Guide](../modules/caching.md)
> **Package:** `pyfly.cache.adapters.redis`
> **Backend:** redis 5.0+ (with hiredis C parser)

## Quick Start

### Installation

```bash
pip install pyfly[cache]

# Or just the Redis client
pip install pyfly[redis]
```

### Minimal Configuration

```yaml
# pyfly.yaml
pyfly:
  cache:
    enabled: true
    provider: "redis"
    redis:
      url: "redis://localhost:6379/0"
```

### Minimal Example

```python
from pyfly.cache import cacheable, cache_evict

@cacheable(key="order:{id}")
async def find_by_id(self, id: int) -> Order:
    return await self._repo.find_by_id(id)

@cache_evict(key="order:{id}")
async def delete_order(self, id: int) -> None:
    await self._repo.delete(id)
```

---

## Configuration Reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `pyfly.cache.enabled` | `bool` | `false` | Enable caching |
| `pyfly.cache.provider` | `str` | `"auto"` | Adapter selection (`auto`, `redis`, `memory`) |
| `pyfly.cache.redis.url` | `str` | `"redis://localhost:6379/0"` | Redis connection URL |
| `pyfly.cache.ttl` | `int` | `300` | Default TTL in seconds |

When `provider` is `"auto"`, PyFly uses Redis if the `redis` library is installed, otherwise falls back to `MemoryCacheAdapter`.

---

## Adapter-Specific Features

### RedisCacheAdapter

Implements `CacheAdapter` using `redis.asyncio.Redis`.

- **Serialization:** Values are JSON-serialized before storage and deserialized on retrieval
- **TTL:** Supports per-key TTL via `timedelta` or the global default
- **Connection validation:** Calls `ping()` on `start()` to verify connectivity

### Operations

| Method | Description |
|--------|-------------|
| `get(key)` | Retrieve and deserialize a cached value |
| `put(key, value, ttl)` | Serialize and store a value with optional TTL |
| `evict(key)` | Remove a key from the cache |
| `exists(key)` | Check if a key exists |
| `clear()` | Flush all keys (uses `flushdb`) |

### In-Memory Fallback

When Redis is not available, `MemoryCacheAdapter` (`pyfly.cache.adapters.memory`) provides the same `CacheAdapter` interface using an in-process dict with TTL support. This is auto-configured when the `redis` library is not installed.

---

## Testing

Use the in-memory adapter for tests — no Redis server needed:

```yaml
# pyfly-test.yaml
pyfly:
  cache:
    provider: "memory"
```

---

## See Also

- [Caching Module Guide](../modules/caching.md) — Full API reference: `@cacheable`, `@cache_evict`, `@cache_put`, cache management
- [Adapter Catalog](README.md)
