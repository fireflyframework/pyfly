"""Tests for @aspect and advice decorators."""

from __future__ import annotations

from pyfly.aop.decorators import (
    after,
    after_returning,
    after_throwing,
    around,
    aspect,
    before,
)


class TestAspectDecorator:
    """@aspect sets the correct class-level attributes."""

    def test_marks_class_as_aspect(self) -> None:
        @aspect
        class MyAspect:
            pass

        assert MyAspect.__pyfly_aspect__ is True

    def test_marks_class_as_injectable(self) -> None:
        @aspect
        class MyAspect:
            pass

        assert MyAspect.__pyfly_injectable__ is True

    def test_sets_stereotype(self) -> None:
        @aspect
        class MyAspect:
            pass

        assert MyAspect.__pyfly_stereotype__ == "aspect"

    def test_sets_singleton_scope(self) -> None:
        @aspect
        class MyAspect:
            pass

        assert MyAspect.__pyfly_scope__ == "SINGLETON"


class TestAdviceDecorators:
    """Each advice decorator sets the correct metadata on the method."""

    def test_before(self) -> None:
        @before("service.*.*")
        def on_before(self, jp):
            pass

        assert on_before.__pyfly_advice_type__ == "before"
        assert on_before.__pyfly_pointcut__ == "service.*.*"

    def test_after_returning(self) -> None:
        @after_returning("service.*.*")
        def on_after_returning(self, jp):
            pass

        assert on_after_returning.__pyfly_advice_type__ == "after_returning"
        assert on_after_returning.__pyfly_pointcut__ == "service.*.*"

    def test_after_throwing(self) -> None:
        @after_throwing("service.*.create")
        def on_after_throwing(self, jp):
            pass

        assert on_after_throwing.__pyfly_advice_type__ == "after_throwing"
        assert on_after_throwing.__pyfly_pointcut__ == "service.*.create"

    def test_after(self) -> None:
        @after("**.*")
        def on_after(self, jp):
            pass

        assert on_after.__pyfly_advice_type__ == "after"
        assert on_after.__pyfly_pointcut__ == "**.*"

    def test_around(self) -> None:
        @around("mymod.MyClass.get_*")
        def on_around(self, jp):
            pass

        assert on_around.__pyfly_advice_type__ == "around"
        assert on_around.__pyfly_pointcut__ == "mymod.MyClass.get_*"

    def test_advice_on_aspect_method(self) -> None:
        """Advice decorators work on methods inside an @aspect class."""

        @aspect
        class LoggingAspect:
            @before("service.*.*")
            def log_before(self, jp):
                pass

        method = LoggingAspect.log_before
        assert method.__pyfly_advice_type__ == "before"
        assert method.__pyfly_pointcut__ == "service.*.*"
        assert LoggingAspect.__pyfly_aspect__ is True
