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
"""SQLAlchemy data access adapter — default RepositoryPort implementation."""

from pyfly.data.adapters.sqlalchemy.entity import Base, BaseEntity
from pyfly.data.adapters.sqlalchemy.post_processor import RepositoryBeanPostProcessor
from pyfly.data.adapters.sqlalchemy.query_compiler import QueryMethodCompiler
from pyfly.data.adapters.sqlalchemy.repository import Repository
from pyfly.data.adapters.sqlalchemy.transactional import reactive_transactional

__all__ = [
    "Base",
    "BaseEntity",
    "QueryMethodCompiler",
    "Repository",
    "RepositoryBeanPostProcessor",
    "reactive_transactional",
]
