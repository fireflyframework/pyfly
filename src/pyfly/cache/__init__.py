"""PyFly Cache — Cache abstraction with automatic failover."""

from pyfly.cache.adapters.memory import InMemoryCache
from pyfly.cache.adapters.redis import RedisCacheAdapter
from pyfly.cache.decorators import cache
from pyfly.cache.manager import CacheManager
from pyfly.cache.ports.outbound import CacheAdapter

__all__ = [
    "CacheAdapter",
    "CacheManager",
    "InMemoryCache",
    "RedisCacheAdapter",
    "cache",
]
