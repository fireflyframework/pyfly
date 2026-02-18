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
"""Tests for AdminLogHandler ring buffer."""

import logging

from pyfly.admin.log_handler import AdminLogHandler


class TestAdminLogHandler:
    def test_captures_log_records(self):
        handler = AdminLogHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger = logging.getLogger("test.capture")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        try:
            logger.info("hello world")
            logger.warning("watch out")

            records = handler.get_all()
            assert len(records) == 2
            assert records[0]["message"] == "hello world"
            assert records[0]["level"] == "INFO"
            assert records[1]["message"] == "watch out"
            assert records[1]["level"] == "WARNING"
        finally:
            logger.removeHandler(handler)

    def test_ring_buffer_evicts_old(self):
        handler = AdminLogHandler(max_records=3)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger = logging.getLogger("test.evict")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        try:
            for i in range(5):
                logger.info(f"msg-{i}")

            records = handler.get_all()
            assert len(records) == 3
            # Oldest two (msg-0, msg-1) should have been evicted
            assert records[0]["message"] == "msg-2"
            assert records[1]["message"] == "msg-3"
            assert records[2]["message"] == "msg-4"
        finally:
            logger.removeHandler(handler)

    def test_get_records_after_id(self):
        handler = AdminLogHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger = logging.getLogger("test.after")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        try:
            logger.info("first")
            logger.info("second")
            logger.info("third")

            # Get records after id=1 (should skip "first")
            records = handler.get_records(after=1)
            assert len(records) == 2
            assert records[0]["message"] == "second"
            assert records[1]["message"] == "third"

            # Get records after id=3 (should return empty)
            records = handler.get_records(after=3)
            assert len(records) == 0
        finally:
            logger.removeHandler(handler)

    def test_clear(self):
        handler = AdminLogHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger = logging.getLogger("test.clear")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        try:
            logger.info("will be cleared")
            assert len(handler.get_all()) == 1

            handler.clear()
            assert len(handler.get_all()) == 0
        finally:
            logger.removeHandler(handler)

    def test_record_format(self):
        handler = AdminLogHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger = logging.getLogger("test.format")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        try:
            logger.error("kaboom")

            records = handler.get_all()
            assert len(records) == 1
            record = records[0]

            assert "id" in record
            assert "timestamp" in record
            assert "level" in record
            assert "logger" in record
            assert "message" in record
            assert "thread" in record

            assert record["level"] == "ERROR"
            assert record["logger"] == "test.format"
            assert record["message"] == "kaboom"
            assert isinstance(record["id"], int)
            # Timestamp should be ISO format with timezone
            assert "T" in record["timestamp"]
        finally:
            logger.removeHandler(handler)
