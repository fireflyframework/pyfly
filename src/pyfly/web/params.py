"""Request binding types for controller handler methods.

Usage in handler signatures::

    async def get_order(self, order_id: PathVar[str]) -> OrderResponse: ...
    async def list_orders(self, page: QueryParam[int] = 1) -> list: ...
    async def create_order(self, body: Body[CreateOrderRequest]) -> OrderResponse: ...
    async def get_with_auth(self, token: Header[str]) -> dict: ...
    async def tracked(self, session: Cookie[str]) -> dict: ...
"""

from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class PathVar(Generic[T]):
    """Path variable extracted from the URL path (e.g. ``/orders/{order_id}``)."""


class QueryParam(Generic[T]):
    """Query parameter extracted from the URL query string (e.g. ``?page=1``)."""


class Body(Generic[T]):
    """JSON request body, validated via Pydantic when T is a BaseModel."""


class Header(Generic[T]):
    """HTTP header value. Parameter name is converted: ``x_api_key`` -> ``x-api-key``."""


class Cookie(Generic[T]):
    """Cookie value extracted from the request."""
