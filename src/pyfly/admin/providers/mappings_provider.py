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
"""Request mappings data provider."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyfly.context.application_context import ApplicationContext


class MappingsProvider:
    """Provides HTTP request mapping metadata."""

    def __init__(self, context: ApplicationContext) -> None:
        self._context = context

    async def get_mappings(self) -> dict[str, Any]:
        mappings: list[dict[str, Any]] = []
        for cls, _reg in self._context.container._registrations.items():
            if getattr(cls, "__pyfly_stereotype__", "") != "rest_controller":
                continue
            base_path = getattr(cls, "__pyfly_request_mapping__", "")
            tag = cls.__name__

            for attr_name in dir(cls):
                method_obj = getattr(cls, attr_name, None)
                if method_obj is None:
                    continue
                mapping = getattr(method_obj, "__pyfly_mapping__", None)
                if mapping is None:
                    continue
                mappings.append({
                    "controller": tag,
                    "method": mapping["method"],
                    "path": base_path + mapping["path"],
                    "handler": attr_name,
                    "status_code": mapping.get("status_code", 200),
                })
        mappings.sort(key=lambda m: m["path"])
        return {"mappings": mappings, "total": len(mappings)}
