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
"""Tests for the metrics actuator endpoint stub."""

from __future__ import annotations

import pytest

from pyfly.actuator.endpoints import MetricsEndpoint


class TestMetricsEndpoint:
    def test_endpoint_id(self):
        ep = MetricsEndpoint()
        assert ep.endpoint_id == "metrics"

    def test_disabled_by_default(self):
        ep = MetricsEndpoint()
        assert ep.enabled is False

    @pytest.mark.asyncio
    async def test_handle_returns_stub_data(self):
        ep = MetricsEndpoint()
        data = await ep.handle()
        assert "names" in data
        assert isinstance(data["names"], list)
        assert "message" in data
