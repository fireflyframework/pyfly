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
"""Logfile data provider -- log record listing and management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyfly.admin.log_handler import AdminLogHandler


class LogfileProvider:
    """Provides log records from the in-memory AdminLogHandler."""

    def __init__(self, log_handler: AdminLogHandler) -> None:
        self._handler = log_handler

    async def get_logfile(self) -> dict[str, Any]:
        records = self._handler.get_all()
        return {
            "available": True,
            "records": records,
            "total": len(records),
        }

    async def clear_logfile(self) -> dict[str, Any]:
        self._handler.clear()
        return {"cleared": True}
