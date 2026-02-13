"""PyFlyRouter — route registration with OpenAPI metadata collection."""

from __future__ import annotations

import functools
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel
from starlette.requests import Request
from starlette.routing import Mount, Route


@dataclass
class RouteMetadata:
    """Metadata for a single route, consumed by the OpenAPI schema generator."""

    path: str
    method: str
    handler: Any
    summary: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    request_model: type[BaseModel] | None = None
    response_model: type[BaseModel] | None = None
    status_code: int = 200
    deprecated: bool = False


class PyFlyRouter:
    """Collects route handlers and their OpenAPI metadata at decoration time.

    Usage::

        router = PyFlyRouter(prefix="/api/items", tags=["Items"])

        @router.get("/{item_id}", response_model=ItemResponse, summary="Get item")
        async def get_item(request: Request) -> JSONResponse:
            ...

    The collected metadata can later be fed to the OpenAPI schema generator via
    ``get_route_metadata()``, and Starlette-compatible routes are produced by
    ``to_starlette_routes()``.
    """

    def __init__(self, prefix: str = "", tags: list[str] | None = None) -> None:
        self._prefix = prefix.rstrip("/")
        self._default_tags = tags or []
        self._routes: list[RouteMetadata] = []

    # ------------------------------------------------------------------
    # Public HTTP-method decorators
    # ------------------------------------------------------------------

    def get(self, path: str, **kwargs: Any):
        """Register a GET handler."""
        return self._route("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any):
        """Register a POST handler."""
        return self._route("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any):
        """Register a PUT handler."""
        return self._route("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any):
        """Register a PATCH handler."""
        return self._route("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any):
        """Register a DELETE handler."""
        return self._route("DELETE", path, **kwargs)

    # ------------------------------------------------------------------
    # Metadata access
    # ------------------------------------------------------------------

    def get_route_metadata(self) -> list[RouteMetadata]:
        """Return a copy of all collected route metadata."""
        return list(self._routes)

    # ------------------------------------------------------------------
    # Starlette integration
    # ------------------------------------------------------------------

    def to_starlette_routes(self) -> Mount:
        """Convert collected routes into a Starlette ``Mount``."""
        starlette_routes: list[Route] = []
        for meta in self._routes:
            starlette_routes.append(
                Route(
                    meta.path,
                    endpoint=meta.handler,
                    methods=[meta.method],
                ),
            )
        return Mount("", routes=starlette_routes)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _route(
        self,
        method: str,
        path: str,
        *,
        summary: str = "",
        description: str = "",
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        status_code: int = 200,
        tags: list[str] | None = None,
        deprecated: bool = False,
    ):
        full_path = self._prefix + path
        merged_tags = tags if tags is not None else list(self._default_tags)

        def decorator(func):
            meta = RouteMetadata(
                path=full_path,
                method=method,
                handler=func,
                summary=summary,
                description=description,
                tags=merged_tags,
                request_model=request_model,
                response_model=response_model,
                status_code=status_code,
                deprecated=deprecated,
            )
            self._routes.append(meta)

            @functools.wraps(func)
            async def wrapper(request: Request):
                return await func(request)

            wrapper.__pyfly_route_meta__ = meta  # type: ignore[attr-defined]
            return wrapper

        return decorator
