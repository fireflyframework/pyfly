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
"""Tests for CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from pyfly.cli.main import cli


class TestCLI:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "PyFly" in result.output

    def test_help_shows_copyright(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Copyright 2026 Firefly Software Solutions Inc." in result.output
        assert "Apache 2.0 License" in result.output

    def test_new_command_creates_project(self, tmp_path: Path):
        runner = CliRunner()
        project_name = "order-service"
        result = runner.invoke(cli, ["new", project_name, "--directory", str(tmp_path)])
        assert result.exit_code == 0, result.output

        project_dir = tmp_path / project_name
        assert project_dir.exists()
        assert (project_dir / "pyproject.toml").exists()
        assert (project_dir / "src" / "order_service" / "__init__.py").exists()
        assert (project_dir / "tests" / "conftest.py").exists()
        assert (project_dir / "pyfly.yaml").exists()

    def test_new_command_library_archetype(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, ["new", "common-lib", "--archetype", "library", "--directory", str(tmp_path)])
        assert result.exit_code == 0, result.output

        project_dir = tmp_path / "common-lib"
        assert project_dir.exists()
        assert (project_dir / "pyproject.toml").exists()
        assert not (project_dir / "pyfly.yaml").exists()

    def test_new_command_pyproject_content(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, ["new", "my-service", "--directory", str(tmp_path)])
        assert result.exit_code == 0, result.output

        content = (tmp_path / "my-service" / "pyproject.toml").read_text()
        assert 'name = "my-service"' in content
        assert "pyfly" in content

    def test_new_command_with_existing_dir_fails(self, tmp_path: Path):
        runner = CliRunner()
        (tmp_path / "existing").mkdir()
        result = runner.invoke(cli, ["new", "existing", "--directory", str(tmp_path)])
        assert result.exit_code != 0


class TestNewWebApi:
    """Tests for the web-api archetype."""

    def test_web_api_creates_full_structure(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "item-api", "--archetype", "web-api", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

        p = tmp_path / "item-api"
        pkg = p / "src" / "item_api"

        # Core files
        assert (p / "pyproject.toml").exists()
        assert (p / "pyfly.yaml").exists()
        assert (p / "Dockerfile").exists()
        assert (p / "README.md").exists()
        assert (p / ".gitignore").exists()
        assert (p / ".env.example").exists()

        # Layered package structure
        assert (pkg / "app.py").exists()
        assert (pkg / "controllers" / "health_controller.py").exists()
        assert (pkg / "controllers" / "item_controller.py").exists()
        assert (pkg / "services" / "item_service.py").exists()
        assert (pkg / "models" / "item.py").exists()
        assert (pkg / "repositories" / "item_repository.py").exists()

        # Test file
        assert (p / "tests" / "test_item_controller.py").exists()

    def test_web_api_controller_uses_stereotypes(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-api", "--archetype", "web-api", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

        controller = (tmp_path / "my-api" / "src" / "my_api" / "controllers" / "item_controller.py").read_text()
        assert "@rest_controller" in controller
        assert "@request_mapping" in controller
        assert "@get_mapping" in controller
        assert "@post_mapping" in controller
        assert "from pyfly.container import rest_controller" in controller

    def test_web_api_service_uses_stereotype(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-api", "--archetype", "web-api", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

        service = (tmp_path / "my-api" / "src" / "my_api" / "services" / "item_service.py").read_text()
        assert "@service" in service
        assert "from pyfly.container import service" in service

    def test_web_api_repository_uses_stereotype(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-api", "--archetype", "web-api", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

        repo = (tmp_path / "my-api" / "src" / "my_api" / "repositories" / "item_repository.py").read_text()
        assert "@repository" in repo
        assert "from pyfly.container import repository" in repo

    def test_web_api_app_scan_packages(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-api", "--archetype", "web-api", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

        app = (tmp_path / "my-api" / "src" / "my_api" / "app.py").read_text()
        assert "my_api.controllers" in app
        assert "my_api.services" in app
        assert "my_api.repositories" in app

    def test_web_api_default_features_web(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-api", "--archetype", "web-api", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

        pyproject = (tmp_path / "my-api" / "pyproject.toml").read_text()
        assert "pyfly[web]" in pyproject


class TestNewHexagonal:
    """Tests for the hexagonal archetype."""

    def test_hexagonal_creates_full_structure(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "order-svc", "--archetype", "hexagonal", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

        p = tmp_path / "order-svc"
        pkg = p / "src" / "order_svc"

        # Core files
        assert (p / "pyproject.toml").exists()
        assert (p / "pyfly.yaml").exists()
        assert (p / "Dockerfile").exists()
        assert (p / "README.md").exists()

        # Hexagonal layers
        assert (pkg / "domain" / "models.py").exists()
        assert (pkg / "domain" / "events.py").exists()
        assert (pkg / "domain" / "ports" / "inbound.py").exists()
        assert (pkg / "domain" / "ports" / "outbound.py").exists()
        assert (pkg / "application" / "services.py").exists()
        assert (pkg / "infrastructure" / "adapters" / "persistence.py").exists()
        assert (pkg / "infrastructure" / "config.py").exists()
        assert (pkg / "api" / "controllers.py").exists()
        assert (pkg / "api" / "dto.py").exists()

        # Tests by layer
        assert (p / "tests" / "domain" / "test_models.py").exists()
        assert (p / "tests" / "application" / "test_services.py").exists()

    def test_hexagonal_uses_protocol_ports(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-hex", "--archetype", "hexagonal", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

        inbound = (tmp_path / "my-hex" / "src" / "my_hex" / "domain" / "ports" / "inbound.py").read_text()
        assert "Protocol" in inbound
        assert "class CreateItemUseCase" in inbound

    def test_hexagonal_app_scan_packages(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-hex", "--archetype", "hexagonal", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

        app = (tmp_path / "my-hex" / "src" / "my_hex" / "app.py").read_text()
        assert "my_hex.api" in app
        assert "my_hex.application" in app
        assert "my_hex.infrastructure" in app


class TestNewFeatures:
    """Tests for the --features flag."""

    def test_features_flag_sets_dependencies(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-svc", "--features", "web,data,cache", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

        pyproject = (tmp_path / "my-svc" / "pyproject.toml").read_text()
        assert "pyfly[web,data,cache]" in pyproject

    def test_features_affect_config(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-svc", "--features", "web,data", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

        config = (tmp_path / "my-svc" / "pyfly.yaml").read_text()
        assert "data:" in config
        assert "datasource:" in config
        assert "port: 8080" in config

    def test_features_data_adds_database_url_to_env(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-svc", "--features", "data", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

        env = (tmp_path / "my-svc" / ".env.example").read_text()
        assert "DATABASE_URL" in env

    def test_features_cache_adds_redis_to_config(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-svc", "--features", "cache", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

        config = (tmp_path / "my-svc" / "pyfly.yaml").read_text()
        assert "cache:" in config
        assert "redis:" in config

    def test_invalid_feature_fails(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-svc", "--features", "web,nosuchfeature", "--directory", str(tmp_path),
        ])
        assert result.exit_code != 0

    def test_no_features_for_library(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-lib", "--archetype", "library", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

        pyproject = (tmp_path / "my-lib" / "pyproject.toml").read_text()
        # Library with no features should have bare pyfly dependency
        assert '"pyfly"' in pyproject


class TestNewEnhancedCore:
    """Tests for enhanced core archetype."""

    def test_core_has_dockerfile(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-svc", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output
        assert (tmp_path / "my-svc" / "Dockerfile").exists()

    def test_core_has_readme(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-svc", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output
        assert (tmp_path / "my-svc" / "README.md").exists()

    def test_core_has_env_example(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-svc", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output
        assert (tmp_path / "my-svc" / ".env.example").exists()

    def test_core_dockerfile_multi_stage(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-svc", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

        dockerfile = (tmp_path / "my-svc" / "Dockerfile").read_text()
        assert "FROM python:3.12-slim AS builder" in dockerfile
        assert "FROM python:3.12-slim" in dockerfile
        assert "EXPOSE 8080" in dockerfile


class TestNewEnhancedLibrary:
    """Tests for enhanced library archetype."""

    def test_library_has_py_typed(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-lib", "--archetype", "library", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output
        assert (tmp_path / "my-lib" / "src" / "my_lib" / "py.typed").exists()

    def test_library_has_readme(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-lib", "--archetype", "library", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

        readme = (tmp_path / "my-lib" / "README.md").read_text()
        assert "my-lib" in readme
        assert "library" in readme.lower()

    def test_library_no_dockerfile(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-lib", "--archetype", "library", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output
        # Libraries don't need a Dockerfile
        assert not (tmp_path / "my-lib" / "Dockerfile").exists()

    def test_library_no_pyfly_yaml(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "my-lib", "--archetype", "library", "--directory", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output
        assert not (tmp_path / "my-lib" / "pyfly.yaml").exists()


class TestNewInteractive:
    """Tests for interactive mode (no NAME argument)."""

    def test_interactive_creates_project(self, tmp_path: Path):
        runner = CliRunner()
        # Simulate: name=test-svc, package=test_svc (default), archetype=1 (core), features="" (defaults)
        user_input = f"test-svc\n\n1\n\n"
        result = runner.invoke(
            cli,
            ["new", "--directory", str(tmp_path)],
            input=user_input,
        )
        assert result.exit_code == 0, result.output
        assert (tmp_path / "test-svc").exists()
        assert (tmp_path / "test-svc" / "pyproject.toml").exists()

    def test_interactive_web_api(self, tmp_path: Path):
        runner = CliRunner()
        # Simulate: name=my-api, package=my_api (default), archetype=2 (web-api), features=web (default)
        user_input = f"my-api\n\n2\nweb\n"
        result = runner.invoke(
            cli,
            ["new", "--directory", str(tmp_path)],
            input=user_input,
        )
        assert result.exit_code == 0, result.output

        p = tmp_path / "my-api"
        assert (p / "src" / "my_api" / "controllers" / "item_controller.py").exists()


class TestInfoCommand:
    def test_info_shows_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["info"])
        assert result.exit_code == 0
        assert "PyFly Framework" in result.output
        assert "0.1.0" in result.output

    def test_info_shows_python_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["info"])
        assert result.exit_code == 0
        assert "Python" in result.output

    def test_info_shows_extras(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["info"])
        assert result.exit_code == 0
        assert "Installed Extras" in result.output
        assert "web" in result.output


class TestRunCommand:
    def test_run_without_app_or_config_fails(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(cli, ["run"], catch_exceptions=False)
        assert result.exit_code != 0
        assert "No application found" in result.output

    def test_run_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        assert "--host" in result.output
        assert "--port" in result.output
        assert "--reload" in result.output


class TestDoctorCommand:
    def test_doctor_runs(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0
        assert "PyFly Doctor" in result.output

    def test_doctor_checks_python(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0
        assert "Python" in result.output

    def test_doctor_checks_tools(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0
        # git should be found in any dev environment
        assert "git" in result.output
