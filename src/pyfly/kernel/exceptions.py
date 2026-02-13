"""Unified exception hierarchy for PyFly.

All framework exceptions inherit from PyFlyException, enabling unified
error handling across modules. Mirrors fireflyframework-kernel's design.

Categories:
- BusinessException: Domain rule violations, validation errors
- InfrastructureException: Database, cache, messaging, network failures
- SecurityException: Authentication and authorization errors
"""

from __future__ import annotations


class PyFlyException(Exception):
    """Base exception for all PyFly errors.

    Carries an optional error code and context dict for structured error data.
    This enables unified exception handling: catch PyFlyException to handle
    all framework errors, or catch specific subclasses for targeted handling.

    Args:
        message: Human-readable error description.
        code: Machine-readable error code (e.g. "VALIDATION_001").
        context: Arbitrary key-value pairs for error context and debugging.
    """

    def __init__(
        self,
        message: str,
        code: str | None = None,
        context: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.context: dict = context if context is not None else {}


class InfrastructureException(PyFlyException):
    """Infrastructure failures: database, cache, messaging, network."""


class SecurityException(PyFlyException):
    """Authentication and authorization errors."""


class BusinessException(PyFlyException):
    """Domain rule violations and business logic errors."""


class ValidationException(BusinessException):
    """Input validation failures."""


class ResourceNotFoundException(BusinessException):
    """Requested resource does not exist."""


class ConflictException(BusinessException):
    """Operation conflicts with current state (e.g. duplicate, version mismatch)."""


class RateLimitException(InfrastructureException):
    """Request rate limit exceeded."""


class CircuitBreakerException(InfrastructureException):
    """Circuit breaker is open, operation rejected."""


class ServiceUnavailableException(InfrastructureException):
    """Downstream service is unavailable."""
