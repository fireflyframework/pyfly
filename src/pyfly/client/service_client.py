"""HTTP service client builder with resilience patterns."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import httpx

from pyfly.client.circuit_breaker import CircuitBreaker
from pyfly.client.retry import RetryPolicy


class ServiceClient:
    """Resilient HTTP client with circuit breaker and retry support.

    Built on httpx with a fluent builder API:

        client = (ServiceClient.rest("user-service")
            .base_url("http://localhost:8081")
            .timeout(timedelta(seconds=10))
            .circuit_breaker(failure_threshold=5)
            .retry(max_attempts=3)
            .build())

        response = await client.get("/users/123")
    """

    def __init__(
        self,
        name: str,
        http_client: httpx.AsyncClient,
        breaker: CircuitBreaker | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.name = name
        self._client = http_client
        self._breaker = breaker
        self._retry = retry_policy

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Send a GET request."""
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Send a POST request."""
        return await self._request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> httpx.Response:
        """Send a PUT request."""
        return await self._request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """Send a DELETE request."""
        return await self._request("DELETE", path, **kwargs)

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Execute an HTTP request with resilience patterns."""

        async def do_request() -> httpx.Response:
            return await self._client.request(method, path, **kwargs)

        operation = do_request

        if self._breaker is not None:
            original = operation

            async def with_breaker() -> httpx.Response:
                return await self._breaker.call(original)

            operation = with_breaker

        if self._retry is not None:
            final_op = operation

            async def with_retry() -> httpx.Response:
                return await self._retry.execute(final_op)

            operation = with_retry

        return await operation()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    @staticmethod
    def rest(name: str) -> ServiceClientBuilder:
        """Create a builder for a REST service client."""
        return ServiceClientBuilder(name)


class ServiceClientBuilder:
    """Fluent builder for ServiceClient."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._base_url: str = ""
        self._timeout: timedelta = timedelta(seconds=30)
        self._breaker: CircuitBreaker | None = None
        self._retry: RetryPolicy | None = None
        self._headers: dict[str, str] = {}

    def base_url(self, url: str) -> ServiceClientBuilder:
        """Set the base URL for all requests."""
        self._base_url = url
        return self

    def timeout(self, timeout: timedelta) -> ServiceClientBuilder:
        """Set the request timeout."""
        self._timeout = timeout
        return self

    def circuit_breaker(
        self,
        failure_threshold: int = 5,
        recovery_timeout: timedelta = timedelta(seconds=30),
    ) -> ServiceClientBuilder:
        """Enable circuit breaker."""
        self._breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
        return self

    def retry(
        self,
        max_attempts: int = 3,
        base_delay: timedelta = timedelta(seconds=1),
    ) -> ServiceClientBuilder:
        """Enable retry with exponential backoff."""
        self._retry = RetryPolicy(
            max_attempts=max_attempts,
            base_delay=base_delay,
        )
        return self

    def header(self, name: str, value: str) -> ServiceClientBuilder:
        """Add a default header."""
        self._headers[name] = value
        return self

    def build(self) -> ServiceClient:
        """Build the ServiceClient."""
        http_client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout.total_seconds(),
            headers=self._headers,
        )
        return ServiceClient(
            name=self._name,
            http_client=http_client,
            breaker=self._breaker,
            retry_policy=self._retry,
        )
