"""Security context for request-scoped authentication and authorization."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SecurityContext:
    """Holds authentication and authorization data for the current request.

    Typically populated from a JWT token by middleware and injected into
    handler functions via the DI container or as a parameter.
    """

    user_id: str | None = None
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    attributes: dict[str, str] = field(default_factory=dict)

    @property
    def is_authenticated(self) -> bool:
        """Whether the current user is authenticated."""
        return self.user_id is not None

    def has_role(self, role: str) -> bool:
        """Check if the user has a specific role."""
        return role in self.roles

    def has_any_role(self, roles: list[str]) -> bool:
        """Check if the user has any of the specified roles."""
        return bool(set(self.roles) & set(roles))

    def has_permission(self, permission: str) -> bool:
        """Check if the user has a specific permission."""
        return permission in self.permissions

    @classmethod
    def anonymous(cls) -> SecurityContext:
        """Create an anonymous (unauthenticated) security context."""
        return cls()
