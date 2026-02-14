# Copyright 2026 Firefly Software Solutions Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""OpenAPI 3.1 schema generator."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from pyfly.web.controller import RouteMetadata

_PATH_PARAM_RE = re.compile(r"\{(\w+)\}")


class OpenAPIGenerator:
    """Generate an OpenAPI 3.1 specification dict.

    Usage::

        gen = OpenAPIGenerator(title="My API", version="1.0.0")
        spec = gen.generate()                       # empty paths
        spec = gen.generate(route_metadata=metadata) # real paths
    """

    def __init__(
        self,
        title: str,
        version: str,
        description: str = "",
    ) -> None:
        self._title = title
        self._version = version
        self._description = description
        self._schemas: dict[str, Any] = {}

    def generate(
        self, route_metadata: list[RouteMetadata] | None = None
    ) -> dict[str, Any]:
        """Generate a complete OpenAPI 3.1 spec as a dict.

        When *route_metadata* is provided, builds real path items from
        controller handler metadata.  Otherwise returns empty paths.
        """
        self._schemas = {}

        paths: dict[str, Any] = {}
        if route_metadata:
            paths = self._build_paths(route_metadata)

        spec: dict[str, Any] = {
            "openapi": "3.1.0",
            "info": self._build_info(),
            "paths": paths,
        }

        if self._schemas:
            spec["components"] = {"schemas": self._schemas}

        return spec

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    def _build_info(self) -> dict[str, Any]:
        info: dict[str, Any] = {
            "title": self._title,
            "version": self._version,
        }
        if self._description:
            info["description"] = self._description
        return info

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------

    def _build_paths(
        self, route_metadata: list[RouteMetadata]
    ) -> dict[str, Any]:
        """Build the ``paths`` dict from a list of RouteMetadata."""
        paths: dict[str, Any] = {}

        for meta in route_metadata:
            path = meta.path
            method_key = meta.http_method.lower()

            if path not in paths:
                paths[path] = {}

            operation: dict[str, Any] = {
                "operationId": meta.handler_name,
                "responses": self._build_responses(meta),
            }

            if meta.parameters:
                operation["parameters"] = meta.parameters

            if meta.request_body_model is not None:
                ref = self._register_model(meta.request_body_model)
                operation["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": ref},
                        }
                    },
                }

            paths[path][method_key] = operation

        return paths

    # ------------------------------------------------------------------
    # Responses
    # ------------------------------------------------------------------

    def _build_responses(self, meta: RouteMetadata) -> dict[str, Any]:
        """Build the ``responses`` dict for a single operation."""
        status = str(meta.status_code)

        if meta.status_code == 204:
            return {status: {"description": "No Content"}}

        return {status: {"description": "Successful response"}}

    # ------------------------------------------------------------------
    # Schema registration
    # ------------------------------------------------------------------

    def _register_model(self, model: type[BaseModel]) -> str:
        """Register a Pydantic model in ``components.schemas`` and return a ``$ref`` string."""
        name = model.__name__
        if name not in self._schemas:
            self._schemas[name] = model.model_json_schema()
        return f"#/components/schemas/{name}"
