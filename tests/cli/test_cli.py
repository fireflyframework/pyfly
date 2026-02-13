"""Tests for CLI: pyfly new command."""

from pathlib import Path

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
        # Library doesn't have pyfly.yaml
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
