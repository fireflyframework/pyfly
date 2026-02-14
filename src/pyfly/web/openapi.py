"""OpenAPI 3.1 schema generator."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

_PATH_PARAM_RE = re.compile(r"\{(\w+)\}")


class OpenAPIGenerator:
    """Generate an OpenAPI 3.1 specification dict.

    Usage::

        gen = OpenAPIGenerator(title="My API", version="1.0.0")
        spec = gen.generate()
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

    def generate(self) -> dict[str, Any]:
        """Generate a complete OpenAPI 3.1 spec as a dict."""
        self._schemas = {}

        spec: dict[str, Any] = {
            "openapi": "3.1.0",
            "info": self._build_info(),
            "paths": {},
        }

        if self._schemas:
            spec["components"] = {"schemas": self._schemas}

        return spec

    def _build_info(self) -> dict[str, Any]:
        info: dict[str, Any] = {
            "title": self._title,
            "version": self._version,
        }
        if self._description:
            info["description"] = self._description
        return info

    def _register_model(self, model: type[BaseModel]) -> str:
        """Register a Pydantic model in ``components.schemas`` and return a ``$ref`` string."""
        name = model.__name__
        if name not in self._schemas:
            self._schemas[name] = model.model_json_schema()
        return f"#/components/schemas/{name}"
