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
"""Tests for LogfileProvider."""

import logging

from pyfly.admin.log_handler import AdminLogHandler
from pyfly.admin.providers.logfile_provider import LogfileProvider


class TestLogfileProvider:
    async def test_get_logfile_returns_records(self):
        handler = AdminLogHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger = logging.getLogger("test.logfile_provider")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        try:
            logger.info("provider test")

            provider = LogfileProvider(handler)
            result = await provider.get_logfile()

            assert result["available"] is True
            assert result["total"] == 1
            assert len(result["records"]) == 1
            assert result["records"][0]["message"] == "provider test"
        finally:
            logger.removeHandler(handler)

    async def test_logfile_available(self):
        handler = AdminLogHandler()
        provider = LogfileProvider(handler)
        result = await provider.get_logfile()

        assert result["available"] is True
        assert result["total"] == 0
        assert result["records"] == []

    async def test_clear_logfile(self):
        handler = AdminLogHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger = logging.getLogger("test.logfile_clear")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        try:
            logger.info("will be cleared")

            provider = LogfileProvider(handler)
            result = await provider.clear_logfile()
            assert result["cleared"] is True

            result = await provider.get_logfile()
            assert result["total"] == 0
        finally:
            logger.removeHandler(handler)
