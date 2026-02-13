"""Tests for named beans, @primary resolution, and Qualifier injection."""

from typing import Annotated, Protocol, runtime_checkable

import pytest

from pyfly.container.bean import Qualifier, primary
from pyfly.container.container import Container
from pyfly.container.stereotypes import component, service
from pyfly.container.types import Scope


@runtime_checkable
class Greeter(Protocol):
    def greet(self) -> str: ...


@component(name="english")
class EnglishGreeter:
    def greet(self) -> str:
        return "Hello"


@component(name="spanish")
@primary
class SpanishGreeter:
    def greet(self) -> str:
        return "Hola"


class TestNamedBeans:
    def test_register_and_resolve_by_name(self):
        c = Container()
        c.register(EnglishGreeter, name="english")
        result = c.resolve_by_name("english")
        assert result.greet() == "Hello"

    def test_resolve_by_name_not_found(self):
        c = Container()
        with pytest.raises(KeyError, match="No bean named"):
            c.resolve_by_name("nonexistent")

    def test_resolve_all_of_type(self):
        c = Container()
        c.register(EnglishGreeter, name="english")
        c.register(SpanishGreeter, name="spanish")
        c.bind(Greeter, EnglishGreeter)
        c.bind(Greeter, SpanishGreeter)
        beans = c.resolve_all(Greeter)
        assert len(beans) >= 2


class TestPrimaryResolution:
    def test_primary_wins_when_multiple(self):
        c = Container()
        c.register(EnglishGreeter, name="english")
        c.register(SpanishGreeter, name="spanish")
        c.bind(Greeter, EnglishGreeter)
        c.bind(Greeter, SpanishGreeter)
        result = c.resolve(Greeter)
        assert result.greet() == "Hola"  # SpanishGreeter is @primary


class TestQualifierInjection:
    def test_qualifier_selects_named_bean(self):
        c = Container()
        c.register(EnglishGreeter, name="english")
        c.register(SpanishGreeter, name="spanish")
        c.bind(Greeter, EnglishGreeter)
        c.bind(Greeter, SpanishGreeter)

        @service
        class GreetService:
            def __init__(self, greeter: Annotated[Greeter, Qualifier("english")]):
                self.greeter = greeter

        c.register(GreetService)
        svc = c.resolve(GreetService)
        assert svc.greeter.greet() == "Hello"
