"""PyFly CQRS — Command/Query Responsibility Segregation."""

from pyfly.cqrs.decorators import command_handler, query_handler
from pyfly.cqrs.mediator import Mediator
from pyfly.cqrs.middleware import CqrsMiddleware, LoggingMiddleware, MetricsMiddleware
from pyfly.cqrs.types import Command, CommandHandler, Query, QueryHandler

__all__ = [
    "Command",
    "CommandHandler",
    "CqrsMiddleware",
    "LoggingMiddleware",
    "Mediator",
    "MetricsMiddleware",
    "Query",
    "QueryHandler",
    "command_handler",
    "query_handler",
]
