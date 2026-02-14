"""PyFly Client — Resilient HTTP client with circuit breaker and retry."""

from pyfly.client.circuit_breaker import CircuitBreaker, CircuitState
from pyfly.client.declarative import delete, get, http_client, patch, post, put
from pyfly.client.ports.outbound import HttpClientPort
from pyfly.client.post_processor import HttpClientBeanPostProcessor
from pyfly.client.retry import RetryPolicy
from pyfly.client.service_client import ServiceClient

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "HttpClientBeanPostProcessor",
    "HttpClientPort",
    "RetryPolicy",
    "ServiceClient",
    "delete",
    "get",
    "http_client",
    "patch",
    "post",
    "put",
]
