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
"""PyFly Data Relational — abstract relational data access layer.

Re-exports from the active relational adapter (SQLAlchemy by default)
plus relational-specific modules (Specification, Filter, Query).
"""

from pyfly.data.relational.filter import FilterOperator, FilterUtils
from pyfly.data.relational.query import QueryExecutor, query
from pyfly.data.relational.specification import Specification
from pyfly.data.relational.sqlalchemy import (
    Base,
    BaseEntity,
    QueryMethodCompiler,
    Repository,
    RepositoryBeanPostProcessor,
    reactive_transactional,
)

__all__ = [
    # Relational-specific modules
    "FilterOperator",
    "FilterUtils",
    "QueryExecutor",
    "Specification",
    "query",
    # Default adapter (SQLAlchemy)
    "Base",
    "BaseEntity",
    "QueryMethodCompiler",
    "Repository",
    "RepositoryBeanPostProcessor",
    "reactive_transactional",
]
