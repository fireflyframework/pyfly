"""Tests for PyFly kernel exception hierarchy."""

from pyfly.kernel.exceptions import PyFlyException


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
