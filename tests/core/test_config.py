"""Tests for configuration system."""

import os
from dataclasses import dataclass
from pathlib import Path

from pyfly.core.config import Config, config_properties


class TestConfig:
    def test_load_from_dict(self):
        config = Config({"app": {"name": "test-service", "port": 8080}})
        assert config.get("app.name") == "test-service"
        assert config.get("app.port") == 8080

    def test_get_with_default(self):
        config = Config({})
        assert config.get("missing.key", "default") == "default"

    def test_get_nested_value(self):
        config = Config({"database": {"pool": {"size": 10}}})
        assert config.get("database.pool.size") == 10

    def test_load_from_yaml_file(self, tmp_path: Path):
        yaml_content = "app:\n  name: my-service\n  port: 9090\n"
        config_file = tmp_path / "pyfly.yaml"
        config_file.write_text(yaml_content)
        config = Config.from_file(config_file)
        assert config.get("app.name") == "my-service"

    def test_env_var_override(self):
        os.environ["PYFLY_APP_NAME"] = "env-service"
        try:
            config = Config({"app": {"name": "file-service"}})
            assert config.get("app.name") == "env-service"
        finally:
            del os.environ["PYFLY_APP_NAME"]


class TestConfigProperties:
    def test_bind_to_dataclass(self):
        @config_properties(prefix="database")
        @dataclass
        class DatabaseConfig:
            url: str = "sqlite:///test.db"
            pool_size: int = 5

        config = Config({"database": {"url": "postgresql://localhost/mydb", "pool_size": 20}})
        db_config = config.bind(DatabaseConfig)
        assert db_config.url == "postgresql://localhost/mydb"
        assert db_config.pool_size == 20

    def test_bind_uses_defaults(self):
        @config_properties(prefix="database")
        @dataclass
        class DatabaseConfig:
            url: str = "sqlite:///default.db"
            pool_size: int = 5

        config = Config({})
        db_config = config.bind(DatabaseConfig)
        assert db_config.url == "sqlite:///default.db"
        assert db_config.pool_size == 5
