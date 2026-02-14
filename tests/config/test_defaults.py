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
"""Tests for framework defaults loading and TOML config support."""

from pathlib import Path

from pyfly.core.config import Config


class TestFrameworkDefaults:
    def test_load_defaults_provides_pyfly_namespace(self):
        defaults = Config._load_framework_defaults()
        assert "pyfly" in defaults
        assert "app" in defaults["pyfly"]

    def test_defaults_have_app_name(self):
        defaults = Config._load_framework_defaults()
        assert defaults["pyfly"]["app"]["name"] == "pyfly-app"

    def test_defaults_have_logging_level(self):
        defaults = Config._load_framework_defaults()
        assert defaults["pyfly"]["logging"]["level"]["root"] == "INFO"

    def test_defaults_have_web_port(self):
        defaults = Config._load_framework_defaults()
        assert defaults["pyfly"]["web"]["port"] == 8080

    def test_defaults_data_disabled(self):
        defaults = Config._load_framework_defaults()
        assert defaults["pyfly"]["data"]["enabled"] is False

    def test_defaults_cache_disabled(self):
        defaults = Config._load_framework_defaults()
        assert defaults["pyfly"]["cache"]["enabled"] is False

    def test_from_file_loads_defaults_automatically(self, tmp_path: Path):
        config_file = tmp_path / "pyfly.yaml"
        config_file.write_text("myapp:\n  custom: true\n")
        config = Config.from_file(config_file)
        # Framework defaults should be present
        assert config.get("pyfly.app.name") == "pyfly-app"
        # User config should also be present
        assert config.get("myapp.custom") is True

    def test_user_config_overrides_defaults(self, tmp_path: Path):
        config_file = tmp_path / "pyfly.yaml"
        config_file.write_text("pyfly:\n  app:\n    name: my-custom-app\n")
        config = Config.from_file(config_file)
        assert config.get("pyfly.app.name") == "my-custom-app"

    def test_from_file_without_defaults(self, tmp_path: Path):
        config_file = tmp_path / "pyfly.yaml"
        config_file.write_text("app:\n  name: test\n")
        config = Config.from_file(config_file, load_defaults=False)
        # Framework defaults should NOT be present
        assert config.get("pyfly.app.name") is None
        # User config should still work
        assert config.get("app.name") == "test"

    def test_missing_file_returns_defaults_only(self, tmp_path: Path):
        config = Config.from_file(tmp_path / "nonexistent.yaml")
        assert config.get("pyfly.app.name") == "pyfly-app"


class TestTomlConfig:
    def test_load_toml_file(self, tmp_path: Path):
        config_file = tmp_path / "pyfly.toml"
        config_file.write_text('[pyfly.app]\nname = "toml-app"\nversion = "2.0.0"\n')
        config = Config.from_file(config_file, load_defaults=False)
        assert config.get("pyfly.app.name") == "toml-app"
        assert config.get("pyfly.app.version") == "2.0.0"

    def test_toml_with_defaults(self, tmp_path: Path):
        config_file = tmp_path / "pyfly.toml"
        config_file.write_text('[pyfly.app]\nname = "toml-app"\n')
        config = Config.from_file(config_file)
        # Overridden by TOML
        assert config.get("pyfly.app.name") == "toml-app"
        # From defaults
        assert config.get("pyfly.web.port") == 8080

    def test_toml_profile_overlay(self, tmp_path: Path):
        base = tmp_path / "pyfly.toml"
        base.write_text('[pyfly.app]\nname = "base-app"\n')
        profile = tmp_path / "pyfly-dev.toml"
        profile.write_text('[pyfly.app]\nname = "dev-app"\ndebug = true\n')
        config = Config.from_file(base, active_profiles=["dev"], load_defaults=False)
        assert config.get("pyfly.app.name") == "dev-app"
        assert config.get("pyfly.app.debug") is True

    def test_toml_nested_tables(self, tmp_path: Path):
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            "[server]\nport = 9090\nhost = \"0.0.0.0\"\n\n"
            "[server.pool]\nsize = 20\n"
        )
        config = Config.from_file(config_file, load_defaults=False)
        assert config.get("server.port") == 9090
        assert config.get("server.pool.size") == 20


class TestConfigEnvVarNormalization:
    def test_pyfly_prefix_stripped_for_env_var(self, monkeypatch):
        monkeypatch.setenv("PYFLY_APP_NAME", "env-app")
        config = Config({})
        # pyfly.app.name should resolve to PYFLY_APP_NAME (not PYFLY_PYFLY_APP_NAME)
        assert config.get("pyfly.app.name") == "env-app"

    def test_non_pyfly_prefix_still_works(self, monkeypatch):
        monkeypatch.setenv("PYFLY_APP_NAME", "env-app")
        config = Config({})
        assert config.get("app.name") == "env-app"

    def test_hyphenated_keys_resolve_env_vars(self, monkeypatch):
        monkeypatch.setenv("PYFLY_DATA_POOL_SIZE", "20")
        config = Config({})
        assert config.get("pyfly.data.pool-size") == "20"


class TestDefaultsNoInfrastructure:
    """Framework defaults must not depend on external infrastructure."""

    def test_messaging_defaults_to_memory(self):
        config = Config(Config._load_framework_defaults())
        assert config.get("pyfly.messaging.provider") == "memory"

    def test_cache_defaults_to_memory(self):
        config = Config(Config._load_framework_defaults())
        assert config.get("pyfly.cache.provider") == "memory"
