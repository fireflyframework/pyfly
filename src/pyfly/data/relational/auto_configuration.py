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
"""Relational data layer (SQLAlchemy) auto-configuration."""

from __future__ import annotations

from pyfly.container.bean import bean
from pyfly.context.conditions import (
    auto_configuration,
    conditional_on_class,
    conditional_on_property,
)
from pyfly.data.relational.sqlalchemy.post_processor import (
    RepositoryBeanPostProcessor,
)


@auto_configuration
@conditional_on_class("sqlalchemy")
@conditional_on_property("pyfly.data.relational.enabled", having_value="true")
class RelationalAutoConfiguration:
    """Auto-configures the SQLAlchemy repository post-processor."""

    @bean
    def repository_post_processor(self) -> RepositoryBeanPostProcessor:
        return RepositoryBeanPostProcessor()
