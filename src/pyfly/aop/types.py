"""AOP core types — JoinPoint dataclass."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class JoinPoint:
    """Represents a point in program execution where advice can be applied.

    Attributes:
        target: The object whose method is being intercepted.
        method_name: Name of the method being called.
        args: Positional arguments passed to the method.
        kwargs: Keyword arguments passed to the method.
        return_value: The return value (set after method execution).
        exception: Any exception raised during execution.
        proceed: Callable to invoke the original method (used in around advice).
    """

    target: Any
    method_name: str
    args: tuple
    kwargs: dict[str, Any]
    return_value: Any = None
    exception: Exception | None = None
    proceed: Callable[..., Any] | None = None
