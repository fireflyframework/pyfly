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
