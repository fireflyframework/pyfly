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
"""Auto-configuration with provider detection (inspired by Spring Boot auto-config)."""

from __future__ import annotations

import importlib


class AutoConfiguration:
    """Detect available infrastructure providers by checking importable packages.

    Similar to Spring Boot's ``@ConditionalOnClass``, each ``detect_*`` method
    probes for well-known libraries and returns a short provider name indicating
    which adapter should be wired.
    """

    @staticmethod
    def is_available(module_name: str) -> bool:
        """Check if a Python package is importable.

        Args:
            module_name: Fully-qualified module name (e.g. ``"redis.asyncio"``).

        Returns:
            ``True`` if the module can be imported, ``False`` otherwise.
        """
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False

    @staticmethod
    def detect_cache_provider() -> str:
        """Detect the best available cache provider.

        Checks for ``redis.asyncio``; falls back to ``"memory"``.
        """
        if AutoConfiguration.is_available("redis.asyncio"):
            return "redis"
        return "memory"

    @staticmethod
    def detect_eda_provider() -> str:
        """Detect the best available event-driven messaging provider.

        Checks for ``aiokafka`` then ``aio_pika``; falls back to ``"memory"``.
        """
        if AutoConfiguration.is_available("aiokafka"):
            return "kafka"
        if AutoConfiguration.is_available("aio_pika"):
            return "rabbitmq"
        return "memory"

    @staticmethod
    def detect_client_provider() -> str:
        """Detect the best available HTTP client provider.

        Checks for ``httpx``; falls back to ``"none"``.
        """
        if AutoConfiguration.is_available("httpx"):
            return "httpx"
        return "none"

    @staticmethod
    def detect_data_provider() -> str:
        """Detect the best available data / ORM provider.

        Checks for ``sqlalchemy``; falls back to ``"none"``.
        """
        if AutoConfiguration.is_available("sqlalchemy"):
            return "sqlalchemy"
        return "none"
