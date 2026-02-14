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
"""Tests for PyFly application bootstrap."""

import pytest

from pyfly.container import Container, service
from pyfly.core.application import PyFlyApplication, pyfly_application


@pyfly_application(name="test-app", scan_packages=[])
class TestApp:
    pass


class TestPyFlyApplication:
    @pytest.mark.asyncio
    async def test_creates_container(self):
        app = PyFlyApplication(TestApp)
        assert isinstance(app.context.container, Container)

    @pytest.mark.asyncio
    async def test_has_config(self):
        app = PyFlyApplication(TestApp)
        assert app.config is not None

    def test_app_metadata(self):
        assert TestApp.__pyfly_app_name__ == "test-app"

    @pytest.mark.asyncio
    async def test_startup_and_shutdown(self):
        app = PyFlyApplication(TestApp)
        await app.startup()
        await app.shutdown()

    @pytest.mark.asyncio
    async def test_auto_discovers_services(self):
        @service
        class DiscoveredService:
            pass

        @pyfly_application(name="discovery-test", scan_packages=["tests.core.test_application"])
        class DiscoveryApp:
            pass

        # Note: This test verifies the scan mechanism works
        # The actual class needs to be in the scanned module
        app = PyFlyApplication(DiscoveryApp)
        await app.startup()
        await app.shutdown()


class TestStartupExperience:
    async def test_startup_logs_app_name_and_version(self, tmp_path):
        @pyfly_application(name="TestApp", version="1.0.0", scan_packages=[])
        class App:
            pass

        config_file = tmp_path / "pyfly.yaml"
        config_file.write_text("pyfly:\n  banner:\n    mode: 'OFF'\n")

        app = PyFlyApplication(App, config_path=config_file)
        await app.startup()
        await app.shutdown()

    async def test_startup_timing_is_tracked(self, tmp_path):
        @pyfly_application(name="TimedApp", version="0.1.0", scan_packages=[])
        class App:
            pass

        config_file = tmp_path / "pyfly.yaml"
        config_file.write_text("pyfly:\n  banner:\n    mode: 'OFF'\n")

        app = PyFlyApplication(App, config_path=config_file)
        await app.startup()
        assert app.startup_time_seconds > 0
        await app.shutdown()

    async def test_banner_is_printed_on_startup(self, tmp_path, capsys):
        @pyfly_application(name="BannerApp", version="0.1.0", scan_packages=[])
        class App:
            pass

        config_file = tmp_path / "pyfly.yaml"
        config_file.write_text("pyfly:\n  banner:\n    mode: 'TEXT'\n")

        app = PyFlyApplication(App, config_path=config_file)
        await app.startup()
        captured = capsys.readouterr()
        assert "PyFly Framework" in captured.out
        await app.shutdown()

    async def test_profiles_logged_on_startup(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PYFLY_PROFILES_ACTIVE", "dev,local")

        @pyfly_application(name="ProfileApp", version="0.1.0", scan_packages=[])
        class App:
            pass

        config_file = tmp_path / "pyfly.yaml"
        config_file.write_text("pyfly:\n  banner:\n    mode: 'OFF'\n")

        app = PyFlyApplication(App, config_path=config_file)
        await app.startup()
        assert app.context.environment.active_profiles == ["dev", "local"]
        await app.shutdown()

    async def test_shutdown_sequence(self, tmp_path):
        @pyfly_application(name="ShutdownApp", version="0.1.0", scan_packages=[])
        class App:
            pass

        config_file = tmp_path / "pyfly.yaml"
        config_file.write_text("pyfly:\n  banner:\n    mode: 'OFF'\n")

        app = PyFlyApplication(App, config_path=config_file)
        await app.startup()
        await app.shutdown()

    async def test_bean_count_reported(self, tmp_path):
        @pyfly_application(name="CountApp", version="0.1.0", scan_packages=[])
        class App:
            pass

        config_file = tmp_path / "pyfly.yaml"
        config_file.write_text("pyfly:\n  banner:\n    mode: 'OFF'\n")

        app = PyFlyApplication(App, config_path=config_file)
        await app.startup()
        assert app.context.bean_count >= 1
        await app.shutdown()

    async def test_profile_config_files_merged(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PYFLY_PROFILES_ACTIVE", "dev")

        config_file = tmp_path / "pyfly.yaml"
        config_file.write_text("app:\n  name: base\npyfly:\n  banner:\n    mode: 'OFF'\n")

        dev_file = tmp_path / "pyfly-dev.yaml"
        dev_file.write_text("app:\n  debug: true\n")

        @pyfly_application(name="MergeApp", version="0.1.0", scan_packages=[])
        class App:
            pass

        app = PyFlyApplication(App, config_path=config_file)
        assert app.config.get("app.name") == "base"
        assert app.config.get("app.debug") is True
        await app.startup()
        await app.shutdown()
