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

PyFly Data is the umbrella module (like Spring Data Commons). It provides
shared abstractions — RepositoryPort[T, ID], QueryMethodParser,
QueryMethodCompilerPort, Page, Pageable — that all data adapters build on.

Adapters:
    - **PyFly Data Relational** (``pyfly.data.adapters.sqlalchemy``) — SQLAlchemy async ORM.
    - **PyFly Data Document** (``pyfly.data.adapters.mongodb``) — MongoDB via Beanie ODM.

Framework-agnostic types (Page, ports) are exported directly.
Default adapter (SQLAlchemy) exports are re-exported for convenience.
"""

# Default adapter (SQLAlchemy) re-exports
from pyfly.data.adapters.sqlalchemy import (
    Base,
    BaseEntity,
    QueryMethodCompiler,
    Repository,
    RepositoryBeanPostProcessor,
    reactive_transactional,
)

# Framework-agnostic exports
from pyfly.data.filter import FilterOperator, FilterUtils
from pyfly.data.mapper import Mapper
from pyfly.data.page import Page
from pyfly.data.pageable import Order, Pageable, Sort
from pyfly.data.ports.compiler import QueryMethodCompilerPort
from pyfly.data.ports.outbound import CrudRepository, PagingRepository, RepositoryPort, SessionPort
from pyfly.data.query import QueryExecutor, query
from pyfly.data.query_parser import QueryMethodParser
from pyfly.data.specification import Specification

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
    "QueryMethodCompilerPort",
    "QueryMethodParser",
    "CrudRepository",
    "PagingRepository",
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

# Optional MongoDB adapter re-exports (available when beanie is installed)
try:
    from pyfly.data.adapters.mongodb import (  # noqa: F401
        BaseDocument,
        MongoQueryMethodCompiler,
        MongoRepository,
        MongoRepositoryBeanPostProcessor,
        mongo_transactional,
    )

    _MONGODB_EXPORTS = [
        "BaseDocument",
        "MongoRepository",
        "MongoQueryMethodCompiler",
        "MongoRepositoryBeanPostProcessor",
        "mongo_transactional",
    ]
except ImportError:
    _MONGODB_EXPORTS = []

__all__ += _MONGODB_EXPORTS
