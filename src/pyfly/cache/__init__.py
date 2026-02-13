"""PyFly Cache — Cache abstraction with automatic failover."""

from pyfly.cache.adapters import InMemoryCache
from pyfly.cache.decorators import cache
from pyfly.cache.manager import CacheManager
from pyfly.cache.types import CacheAdapter

__all__ = [
    "CacheAdapter",
    "CacheManager",
    "InMemoryCache",
    "cache",
]
