"""PyFly DI Container — Pythonic dependency injection."""

from pyfly.container.bean import Qualifier, bean, primary
from pyfly.container.container import Container
from pyfly.container.stereotypes import (
    component,
    configuration,
    controller,
    repository,
    rest_controller,
    service,
)
from pyfly.container.types import Scope

__all__ = [
    "Container",
    "Qualifier",
    "Scope",
    "bean",
    "component",
    "configuration",
    "controller",
    "primary",
    "repository",
    "rest_controller",
    "service",
]
