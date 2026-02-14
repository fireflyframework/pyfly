# Copyright 2026 Firefly Software Solutions Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
