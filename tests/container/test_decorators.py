"""Tests for @injectable decorator."""

from pyfly.container import Container, Scope, injectable


@injectable
class SimpleService:
    pass


@injectable(scope=Scope.TRANSIENT)
class TransientService:
    pass


@injectable(scope=Scope.SINGLETON)
class SingletonService:
    pass


class TestInjectableDecorator:
    def test_marks_class_as_injectable(self):
        assert getattr(SimpleService, "__pyfly_injectable__", False) is True

    def test_preserves_class_identity(self):
        instance = SimpleService()
        assert isinstance(instance, SimpleService)

    def test_default_scope_is_singleton(self):
        assert SimpleService.__pyfly_scope__ == Scope.SINGLETON

    def test_custom_scope(self):
        assert TransientService.__pyfly_scope__ == Scope.TRANSIENT

    def test_injectable_with_explicit_singleton(self):
        assert SingletonService.__pyfly_scope__ == Scope.SINGLETON
