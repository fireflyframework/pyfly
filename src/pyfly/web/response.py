"""Return value handler -- converts handler return values to Starlette Responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from starlette.responses import JSONResponse, Response


def handle_return_value(result: Any, status_code: int = 200) -> Response:
    """Convert a handler's return value into a Starlette Response.

    - ``None`` -> empty response (204 unless status_code explicitly set)
    - ``Response`` -> passed through unchanged
    - ``BaseModel`` -> JSON serialized via model_dump
    - ``dict``, ``list``, ``str``, etc. -> JSON response
    """
    if result is None:
        actual_status = status_code if status_code != 200 else 204
        return Response(status_code=actual_status)

    if isinstance(result, Response):
        return result

    if isinstance(result, BaseModel):
        return JSONResponse(result.model_dump(mode="json"), status_code=status_code)

    return JSONResponse(result, status_code=status_code)
