"""PyFly DI Container — Pythonic dependency injection."""

from pyfly.container.container import Container
from pyfly.container.decorators import injectable
from pyfly.container.types import Scope

__all__ = ["Container", "Scope", "injectable"]
