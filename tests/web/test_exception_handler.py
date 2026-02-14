"""Tests for @exception_handler decorator."""

from pyfly.web.exception_handler import exception_handler


class OrderNotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


class TestExceptionHandler:
    def test_marks_method(self):
        class Ctrl:
            @exception_handler(OrderNotFoundError)
            async def handle_not_found(self, exc):
                return 404, {"error": "not found"}

        meta = Ctrl.handle_not_found.__pyfly_exception_handler__
        assert meta == OrderNotFoundError

    def test_preserves_method(self):
        class Ctrl:
            @exception_handler(OrderNotFoundError)
            async def handle_not_found(self, exc):
                return 404, {"error": "not found"}

        assert callable(Ctrl.handle_not_found)

    def test_multiple_handlers(self):
        class Ctrl:
            @exception_handler(OrderNotFoundError)
            async def handle_not_found(self, exc):
                return 404, {"error": "not found"}

            @exception_handler(ValidationError)
            async def handle_validation(self, exc):
                return 422, {"error": str(exc)}

        assert Ctrl.handle_not_found.__pyfly_exception_handler__ == OrderNotFoundError
        assert Ctrl.handle_validation.__pyfly_exception_handler__ == ValidationError
