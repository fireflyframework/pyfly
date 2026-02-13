"""OpenAPI 3.1 schema generator from PyFlyRouter metadata."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from pyfly.web.router import PyFlyRouter, RouteMetadata

_PATH_PARAM_RE = re.compile(r"\{(\w+)\}")


class OpenAPIGenerator:
    """Generate an OpenAPI 3.1 specification dict from one or more :class:`PyFlyRouter` instances.

    Usage::

        gen = OpenAPIGenerator(
            title="My API",
            version="1.0.0",
            routers=[items_router, users_router],
        )
        spec = gen.generate()  # dict ready for JSON serialisation
    """

    def __init__(
        self,
        title: str,
        version: str,
        routers: list[PyFlyRouter],
        description: str = "",
    ) -> None:
        self._title = title
        self._version = version
        self._routers = routers
        self._description = description
        self._schemas: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self) -> dict[str, Any]:
        """Generate a complete OpenAPI 3.1 spec as a dict."""
        self._schemas = {}
        paths: dict[str, Any] = {}

        for router in self._routers:
            for meta in router.get_route_metadata():
                path = meta.path
                method = meta.method.lower()

                if path not in paths:
                    paths[path] = {}

                paths[path][method] = self._build_operation(meta)

        spec: dict[str, Any] = {
            "openapi": "3.1.0",
            "info": self._build_info(),
            "paths": paths,
        }

        if self._schemas:
            spec["components"] = {"schemas": self._schemas}

        return spec

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_info(self) -> dict[str, Any]:
        info: dict[str, Any] = {
            "title": self._title,
            "version": self._version,
        }
        if self._description:
            info["description"] = self._description
        return info

    def _build_operation(self, meta: RouteMetadata) -> dict[str, Any]:
        operation: dict[str, Any] = {}

        if meta.summary:
            operation["summary"] = meta.summary
        if meta.description:
            operation["description"] = meta.description
        if meta.tags:
            operation["tags"] = meta.tags
        if meta.deprecated:
            operation["deprecated"] = True

        # Path parameters
        params = self._extract_path_params(meta.path)
        if params:
            operation["parameters"] = params

        # Request body
        if meta.request_model is not None:
            ref = self._register_model(meta.request_model)
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": ref},
                    },
                },
            }

        # Responses
        operation["responses"] = self._build_responses(meta)

        return operation

    def _extract_path_params(self, path: str) -> list[dict[str, Any]]:
        """Extract ``{param}`` placeholders from the path and return OpenAPI parameter objects."""
        params: list[dict[str, Any]] = []
        for match in _PATH_PARAM_RE.finditer(path):
            params.append(
                {
                    "name": match.group(1),
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
            )
        return params

    def _build_responses(self, meta: RouteMetadata) -> dict[str, Any]:
        """Build the ``responses`` object for a single operation."""
        status = str(meta.status_code)
        responses: dict[str, Any] = {}

        if meta.response_model is not None:
            ref = self._register_model(meta.response_model)
            responses[status] = {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "schema": {"$ref": ref},
                    },
                },
            }
        else:
            responses[status] = {"description": "Successful response"}

        return responses

    def _register_model(self, model: type[BaseModel]) -> str:
        """Register a Pydantic model in ``components.schemas`` and return a ``$ref`` string."""
        name = model.__name__
        if name not in self._schemas:
            self._schemas[name] = model.model_json_schema()
        return f"#/components/schemas/{name}"
