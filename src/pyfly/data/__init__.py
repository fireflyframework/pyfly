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
"""PyFly Data — Repository pattern with pluggable adapters.

Framework-agnostic types (Page, ports) are exported directly.
Default adapter (SQLAlchemy) exports are re-exported for convenience.
"""

# Framework-agnostic exports
from pyfly.data.filter import FilterOperator, FilterUtils
from pyfly.data.mapper import Mapper
from pyfly.data.page import Page
from pyfly.data.pageable import Order, Pageable, Sort
from pyfly.data.ports.outbound import RepositoryPort, SessionPort
from pyfly.data.query import QueryExecutor, query
from pyfly.data.query_parser import QueryMethodCompiler, QueryMethodParser
from pyfly.data.specification import Specification

# Default adapter (SQLAlchemy) re-exports
from pyfly.data.adapters.sqlalchemy import (
    Base,
    BaseEntity,
    Repository,
    RepositoryBeanPostProcessor,
    reactive_transactional,
)

__all__ = [
    # Framework-agnostic
    "FilterOperator",
    "FilterUtils",
    "Mapper",
    "Order",
    "Page",
    "Pageable",
    "QueryExecutor",
    "QueryMethodCompiler",
    "QueryMethodParser",
    "RepositoryPort",
    "SessionPort",
    "Sort",
    "Specification",
    "query",
    # Default adapter (SQLAlchemy)
    "Base",
    "BaseEntity",
    "Repository",
    "RepositoryBeanPostProcessor",
    "reactive_transactional",
]
