"""Exception converter system — chain of responsibility for exception translation.

Converts external library exceptions (Pydantic, JSON, SQLAlchemy, etc.)
into PyFly exceptions for consistent error handling.
"""

from __future__ import annotations

import json
from typing import Protocol

from pydantic import ValidationError

from pyfly.kernel.exceptions import (
    InvalidRequestException,
    PyFlyException,
    ValidationException,
)


class ExceptionConverter(Protocol):
    """Converts external exceptions to PyFly exceptions."""

    def can_handle(self, exc: Exception) -> bool: ...

    def convert(self, exc: Exception) -> PyFlyException: ...


class ExceptionConverterService:
    """Chain of responsibility for exception conversion.

    Iterates through registered converters and returns the first match.
    """

    def __init__(self, converters: list[ExceptionConverter]) -> None:
        self._converters = converters

    def convert(self, exc: Exception) -> PyFlyException | None:
        """Convert an exception, returning None if no converter matches."""
        for converter in self._converters:
            if converter.can_handle(exc):
                return converter.convert(exc)
        return None


class PydanticExceptionConverter:
    """Converts Pydantic ValidationError to PyFly ValidationException."""

    def can_handle(self, exc: Exception) -> bool:
        return isinstance(exc, ValidationError)

    def convert(self, exc: Exception) -> PyFlyException:
        assert isinstance(exc, ValidationError)
        errors = exc.errors()
        detail = "; ".join(
            f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}" for e in errors
        )
        return ValidationException(
            f"Validation failed: {detail}",
            code="VALIDATION_ERROR",
            context={"errors": errors},
        )


class JSONExceptionConverter:
    """Converts json.JSONDecodeError to PyFly InvalidRequestException."""

    def can_handle(self, exc: Exception) -> bool:
        return isinstance(exc, json.JSONDecodeError)

    def convert(self, exc: Exception) -> PyFlyException:
        assert isinstance(exc, json.JSONDecodeError)
        return InvalidRequestException(
            f"Invalid JSON: {exc.msg}",
            code="INVALID_JSON",
            context={"position": exc.pos},
        )
