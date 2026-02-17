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
"""Loggers data provider — logger listing and level management."""

from __future__ import annotations

import logging
from typing import Any


class LoggersProvider:
    """Provides logger data and level management."""

    async def get_loggers(self) -> dict[str, Any]:
        manager = logging.Logger.manager
        loggers: dict[str, Any] = {}

        root = logging.getLogger()
        loggers["ROOT"] = {
            "configuredLevel": logging.getLevelName(root.level),
            "effectiveLevel": logging.getLevelName(root.getEffectiveLevel()),
        }

        for name in sorted(manager.loggerDict):
            logger_obj = manager.loggerDict[name]
            if isinstance(logger_obj, logging.Logger):
                loggers[name] = {
                    "configuredLevel": (
                        logging.getLevelName(logger_obj.level)
                        if logger_obj.level != logging.NOTSET
                        else None
                    ),
                    "effectiveLevel": logging.getLevelName(logger_obj.getEffectiveLevel()),
                }

        return {
            "loggers": loggers,
            "levels": ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        }

    async def set_level(self, logger_name: str, level: str) -> dict[str, str]:
        target = logging.getLogger() if logger_name == "ROOT" else logging.getLogger(logger_name)
        numeric = getattr(logging, level.upper(), None)
        if numeric is None:
            return {"error": f"Unknown level: {level}"}
        target.setLevel(numeric)
        return {"logger": logger_name, "configuredLevel": level.upper()}
