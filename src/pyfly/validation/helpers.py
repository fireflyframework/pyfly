"""Pydantic integration helpers for validation."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from pyfly.kernel.exceptions import ValidationException

T = TypeVar("T", bound=BaseModel)


def validate_model(model: type[T], data: dict[str, Any]) -> T:
    """Validate data against a Pydantic model.

    Raises:
        ValidationException: If validation fails, with structured error details.
    """
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        errors = exc.errors()
        detail = "; ".join(
            f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}" for e in errors
        )
        raise ValidationException(
            f"Validation failed: {detail}",
            code="VALIDATION_ERROR",
            context={"errors": errors},
        ) from exc
