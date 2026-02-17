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
"""Admin dashboard auto-configuration."""

from __future__ import annotations

from pyfly.admin.config import AdminProperties
from pyfly.admin.middleware.trace_collector import TraceCollectorFilter
from pyfly.admin.registry import AdminViewRegistry
from pyfly.container.bean import bean
from pyfly.context.conditions import (
    auto_configuration,
    conditional_on_class,
    conditional_on_property,
)
from pyfly.core.config import Config


@auto_configuration
@conditional_on_property("pyfly.admin.enabled", having_value="true")
@conditional_on_class("starlette")
class AdminAutoConfiguration:
    """Auto-configures the admin dashboard when enabled."""

    @bean
    def admin_properties(self, config: Config) -> AdminProperties:
        return config.bind(AdminProperties)

    @bean
    def admin_view_registry(self) -> AdminViewRegistry:
        return AdminViewRegistry()

    @bean
    def admin_trace_collector(self) -> TraceCollectorFilter:
        return TraceCollectorFilter()
