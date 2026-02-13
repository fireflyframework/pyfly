"""Security decorators for role-based and permission-based access control."""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, TypeVar

from pyfly.kernel.exceptions import SecurityException
from pyfly.security.context import SecurityContext

F = TypeVar("F", bound=Callable[..., Any])


def secure(
    roles: list[str] | None = None,
    permissions: list[str] | None = None,
) -> Callable[[F], F]:
    """Decorator for securing endpoints with role and permission checks.

    The decorated function must accept a `security_context` keyword argument
    of type SecurityContext.

    Args:
        roles: Required roles (user must have at least one).
        permissions: Required permissions (user must have all).

    Raises:
        SecurityException: If authentication or authorization fails.

    Usage:
        @secure(roles=["ADMIN"], permissions=["order:delete"])
        async def delete_order(order_id: str, security_context: SecurityContext) -> None: ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            ctx: SecurityContext | None = kwargs.get("security_context")
            if ctx is None:
                raise SecurityException("Authentication required", code="AUTH_REQUIRED")

            if not ctx.is_authenticated:
                raise SecurityException("Authentication required", code="AUTH_REQUIRED")

            if roles and not ctx.has_any_role(roles):
                raise SecurityException(
                    f"Insufficient roles: requires one of {roles}",
                    code="FORBIDDEN",
                )

            if permissions:
                missing = [p for p in permissions if not ctx.has_permission(p)]
                if missing:
                    raise SecurityException(
                        f"Insufficient permissions: missing {missing}",
                        code="FORBIDDEN",
                    )

            return await func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
