"""Tests for PyFly kernel exception hierarchy."""

from pyfly.kernel.exceptions import (
    BusinessException,
    CircuitBreakerException,
    ConflictException,
    InfrastructureException,
    PyFlyException,
    RateLimitException,
    ResourceNotFoundException,
    SecurityException,
    ServiceUnavailableException,
    ValidationException,
)


class TestPyFlyException:
    def test_basic_creation(self):
        exc = PyFlyException("something went wrong")
        assert str(exc) == "something went wrong"
        assert exc.code is None
        assert exc.context == {}

    def test_with_error_code(self):
        exc = PyFlyException("bad request", code="VALIDATION_001")
        assert exc.code == "VALIDATION_001"

    def test_with_context(self):
        exc = PyFlyException("not found", code="NOT_FOUND", context={"entity": "Order", "id": "123"})
        assert exc.context["entity"] == "Order"
        assert exc.context["id"] == "123"

    def test_is_runtime_exception(self):
        exc = PyFlyException("test")
        assert isinstance(exc, Exception)

    def test_context_defaults_to_empty_dict(self):
        exc = PyFlyException("test")
        assert exc.context == {}
        # Ensure it's not shared between instances
        exc.context["key"] = "value"
        exc2 = PyFlyException("test2")
        assert exc2.context == {}


class TestExceptionHierarchy:
    def test_business_is_pyfly(self):
        assert issubclass(BusinessException, PyFlyException)

    def test_infrastructure_is_pyfly(self):
        assert issubclass(InfrastructureException, PyFlyException)

    def test_security_is_pyfly(self):
        assert issubclass(SecurityException, PyFlyException)

    def test_validation_is_business(self):
        assert issubclass(ValidationException, BusinessException)

    def test_not_found_is_business(self):
        assert issubclass(ResourceNotFoundException, BusinessException)

    def test_conflict_is_business(self):
        assert issubclass(ConflictException, BusinessException)

    def test_rate_limit_is_infrastructure(self):
        assert issubclass(RateLimitException, InfrastructureException)

    def test_circuit_breaker_is_infrastructure(self):
        assert issubclass(CircuitBreakerException, InfrastructureException)

    def test_service_unavailable_is_infrastructure(self):
        assert issubclass(ServiceUnavailableException, InfrastructureException)

    def test_catch_all_pyfly_exceptions(self):
        """Verify all exceptions can be caught with a single handler."""
        exceptions = [
            ValidationException("bad input"),
            ResourceNotFoundException("missing", code="NOT_FOUND"),
            RateLimitException("too fast"),
            SecurityException("unauthorized"),
            CircuitBreakerException("circuit open"),
        ]
        for exc in exceptions:
            try:
                raise exc
            except PyFlyException as caught:
                assert caught is exc
