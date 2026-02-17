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
"""Beans data provider -- extracts bean metadata from ApplicationContext."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyfly.context.application_context import ApplicationContext


class BeansProvider:
    """Provides detailed bean information for the admin dashboard."""

    def __init__(self, context: ApplicationContext) -> None:
        self._context = context

    async def get_beans(self) -> dict[str, Any]:
        beans: list[dict[str, Any]] = []
        for cls, reg in self._context.container._registrations.items():
            bean_name = reg.name or cls.__name__
            stereotype = getattr(cls, "__pyfly_stereotype__", "none")
            conditions = getattr(cls, "__pyfly_conditions__", [])
            order = getattr(cls, "__pyfly_order__", None)
            profile = getattr(cls, "__pyfly_profile__", None)
            primary = getattr(cls, "__pyfly_primary__", False)

            # Inspect constructor dependencies
            deps = []
            try:
                hints = (
                    inspect.get_annotations(cls.__init__, eval_str=True)
                    if hasattr(cls, "__init__")
                    else {}
                )
                for param_name, param_type in hints.items():
                    if param_name in ("self", "return"):
                        continue
                    deps.append({
                        "name": param_name,
                        "type": getattr(param_type, "__name__", str(param_type)),
                    })
            except Exception:
                pass

            beans.append({
                "name": bean_name,
                "type": f"{cls.__module__}.{cls.__qualname__}",
                "scope": reg.scope.name,
                "stereotype": stereotype,
                "primary": primary,
                "order": order,
                "profile": profile,
                "conditions": [str(c) for c in conditions] if conditions else [],
                "dependencies": deps,
                "initialized": reg.instance is not None,
            })

        beans.sort(key=lambda b: (b["stereotype"], b["name"]))
        return {"beans": beans, "total": len(beans)}

    async def get_bean_detail(self, name: str) -> dict[str, Any] | None:
        for cls, reg in self._context.container._registrations.items():
            bean_name = reg.name or cls.__name__
            if bean_name == name:
                return await self._build_detail(cls, reg)
        return None

    @staticmethod
    def _safe_getfile(cls: type) -> str | None:
        try:
            return inspect.getfile(cls)
        except (TypeError, OSError):
            return None

    async def _build_detail(self, cls: type, reg: Any) -> dict[str, Any]:
        stereotype = getattr(cls, "__pyfly_stereotype__", "none")
        return {
            "name": reg.name or cls.__name__,
            "type": f"{cls.__module__}.{cls.__qualname__}",
            "scope": reg.scope.name,
            "stereotype": stereotype,
            "module": cls.__module__,
            "file": self._safe_getfile(cls),
            "doc": inspect.getdoc(cls) or "",
            "primary": getattr(cls, "__pyfly_primary__", False),
            "order": getattr(cls, "__pyfly_order__", None),
            "profile": getattr(cls, "__pyfly_profile__", None),
            "initialized": reg.instance is not None,
        }
