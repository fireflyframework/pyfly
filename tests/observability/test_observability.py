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
"""Tests for observability module: logging, metrics, tracing, and health."""


import pytest

from pyfly.observability.health import HealthChecker, HealthStatus
from pyfly.observability.logging import configure_logging, get_logger
from pyfly.observability.metrics import MetricsRegistry, counted, timed
from pyfly.observability.tracing import span


class TestStructuredLogging:
    def test_get_logger(self):
        log = get_logger("test.module")
        assert log is not None

    def test_configure_logging_sets_level(self):
        configure_logging(level="DEBUG")
        log = get_logger("test.config")
        assert log is not None


class TestMetrics:
    def test_registry_creates_counter(self):
        registry = MetricsRegistry()
        counter = registry.counter("test_requests_total", "Total requests")
        counter.inc()
        assert counter._value.get() == 1.0

    def test_registry_creates_histogram(self):
        registry = MetricsRegistry()
        histogram = registry.histogram("test_duration_seconds", "Request duration")
        histogram.observe(0.5)

    def test_registry_creates_gauge(self):
        registry = MetricsRegistry()
        gauge = registry.gauge("test_gauge_active_connections", "Active connections")
        gauge.inc()
        gauge.inc()
        gauge.dec()
        assert gauge._value.get() == 1.0

    @pytest.mark.asyncio
    async def test_timed_decorator(self):
        registry = MetricsRegistry()

        @timed(registry, "operation_duration_seconds", "Operation duration")
        async def slow_operation() -> str:
            return "done"

        result = await slow_operation()
        assert result == "done"

    @pytest.mark.asyncio
    async def test_counted_decorator(self):
        registry = MetricsRegistry()

        @counted(registry, "operation_calls_total", "Operation calls")
        async def my_operation() -> str:
            return "ok"

        await my_operation()
        await my_operation()

        counter = registry._counters.get("operation_calls_total")
        assert counter is not None
        assert counter._value.get() == 2.0


class TestTracing:
    @pytest.mark.asyncio
    async def test_span_decorator(self):
        @span("process-order")
        async def process_order(order_id: str) -> dict:
            return {"id": order_id, "status": "processed"}

        result = await process_order("123")
        assert result == {"id": "123", "status": "processed"}

    @pytest.mark.asyncio
    async def test_span_propagates_exceptions(self):
        @span("failing-op")
        async def failing():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            await failing()


class TestHealthChecker:
    @pytest.mark.asyncio
    async def test_healthy_when_no_checks(self):
        checker = HealthChecker()
        result = await checker.check()
        assert result.status == HealthStatus.UP

    @pytest.mark.asyncio
    async def test_healthy_with_passing_check(self):
        checker = HealthChecker()

        async def db_check() -> bool:
            return True

        checker.add_check("database", db_check)
        result = await checker.check()
        assert result.status == HealthStatus.UP
        assert result.checks["database"] == HealthStatus.UP

    @pytest.mark.asyncio
    async def test_unhealthy_with_failing_check(self):
        checker = HealthChecker()

        async def redis_check() -> bool:
            return False

        checker.add_check("redis", redis_check)
        result = await checker.check()
        assert result.status == HealthStatus.DOWN
        assert result.checks["redis"] == HealthStatus.DOWN

    @pytest.mark.asyncio
    async def test_unhealthy_when_check_raises(self):
        checker = HealthChecker()

        async def broken_check() -> bool:
            raise ConnectionError("can't connect")

        checker.add_check("kafka", broken_check)
        result = await checker.check()
        assert result.status == HealthStatus.DOWN
        assert result.checks["kafka"] == HealthStatus.DOWN

    @pytest.mark.asyncio
    async def test_mixed_checks(self):
        checker = HealthChecker()

        async def ok_check() -> bool:
            return True

        async def bad_check() -> bool:
            return False

        checker.add_check("db", ok_check)
        checker.add_check("redis", bad_check)
        result = await checker.check()
        assert result.status == HealthStatus.DOWN
        assert result.checks["db"] == HealthStatus.UP
        assert result.checks["redis"] == HealthStatus.DOWN
