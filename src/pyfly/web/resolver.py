"""ParameterResolver — inspects handler signatures and auto-binds from Request."""

from __future__ import annotations

import inspect
import typing
from dataclasses import dataclass
from typing import Any, get_args, get_origin

from pydantic import BaseModel
from starlette.requests import Request

from pyfly.web.params import Body, Cookie, Header, PathVar, QueryParam

_BINDING_TYPES = {PathVar, QueryParam, Body, Header, Cookie}
_MISSING = object()


@dataclass
class ResolvedParam:
    """Metadata for a single resolved parameter."""

    name: str
    binding_type: type
    inner_type: type
    default: Any = _MISSING


class ParameterResolver:
    """Inspects a handler method's signature and resolves parameters from a Request.

    At startup, inspects type hints to detect PathVar, QueryParam, Body, Header, Cookie.
    At runtime, resolves each parameter from the Starlette Request.
    """

    def __init__(self, handler: Any) -> None:
        self.params = self._inspect(handler)

    def _inspect(self, handler: Any) -> list[ResolvedParam]:
        hints = typing.get_type_hints(handler, include_extras=True)
        sig = inspect.signature(handler)
        params: list[ResolvedParam] = []

        for name, param in sig.parameters.items():
            if name == "self":
                continue

            hint = hints.get(name)
            if hint is None:
                continue

            origin = get_origin(hint)
            if origin not in _BINDING_TYPES:
                continue

            args = get_args(hint)
            inner_type = args[0] if args else str
            default = param.default if param.default is not inspect.Parameter.empty else _MISSING

            params.append(
                ResolvedParam(
                    name=name,
                    binding_type=origin,
                    inner_type=inner_type,
                    default=default,
                )
            )

        return params

    async def resolve(self, request: Request) -> dict[str, Any]:
        """Resolve all parameters from the request."""
        kwargs: dict[str, Any] = {}
        for param in self.params:
            kwargs[param.name] = await self._resolve_one(request, param)
        return kwargs

    async def _resolve_one(self, request: Request, param: ResolvedParam) -> Any:
        if param.binding_type is PathVar:
            return self._resolve_path_var(request, param)
        if param.binding_type is QueryParam:
            return self._resolve_query_param(request, param)
        if param.binding_type is Body:
            return await self._resolve_body(request, param)
        if param.binding_type is Header:
            return self._resolve_header(request, param)
        if param.binding_type is Cookie:
            return self._resolve_cookie(request, param)
        return None  # pragma: no cover

    def _resolve_path_var(self, request: Request, param: ResolvedParam) -> Any:
        raw = request.path_params.get(param.name)
        if raw is None:
            if param.default is not _MISSING:
                return param.default
            msg = f"Missing path variable: {param.name}"
            raise ValueError(msg)
        return self._coerce(raw, param.inner_type)

    def _resolve_query_param(self, request: Request, param: ResolvedParam) -> Any:
        raw = request.query_params.get(param.name)
        if raw is None:
            if param.default is not _MISSING:
                return param.default
            return None
        return self._coerce(raw, param.inner_type)

    async def _resolve_body(self, request: Request, param: ResolvedParam) -> Any:
        body_bytes = await request.body()
        if issubclass(param.inner_type, BaseModel):
            return param.inner_type.model_validate_json(body_bytes)
        return param.inner_type(body_bytes.decode())

    def _resolve_header(self, request: Request, param: ResolvedParam) -> Any:
        header_name = param.name.replace("_", "-")
        raw = request.headers.get(header_name)
        if raw is None:
            if param.default is not _MISSING:
                return param.default
            return None
        return self._coerce(raw, param.inner_type)

    def _resolve_cookie(self, request: Request, param: ResolvedParam) -> Any:
        raw = request.cookies.get(param.name)
        if raw is None:
            if param.default is not _MISSING:
                return param.default
            return None
        return self._coerce(raw, param.inner_type)

    def _coerce(self, value: str, target_type: type) -> Any:
        """Coerce a string value to the target type."""
        if target_type is str:
            return value
        return target_type(value)
