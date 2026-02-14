"""Tests for the install.sh installer script."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


INSTALLER_PATH = Path(__file__).resolve().parent.parent.parent / "install.sh"


@pytest.fixture
def project_root() -> Path:
    return INSTALLER_PATH.parent


class TestInstaller:
    def test_installer_exists(self):
        assert INSTALLER_PATH.exists(), f"install.sh not found at {INSTALLER_PATH}"

    def test_installer_is_executable(self):
        assert os.access(INSTALLER_PATH, os.X_OK), "install.sh is not executable"

    def test_installer_has_shebang(self):
        content = INSTALLER_PATH.read_text()
        assert content.startswith("#!/usr/bin/env bash"), "Missing bash shebang"

    def test_installer_has_set_euo_pipefail(self):
        content = INSTALLER_PATH.read_text()
        assert "set -euo pipefail" in content, "Missing strict mode"

    def test_installer_detects_interactive_mode(self):
        content = INSTALLER_PATH.read_text()
        assert "IS_INTERACTIVE" in content

    def test_installer_checks_python_version(self):
        content = INSTALLER_PATH.read_text()
        assert "MIN_PYTHON_MAJOR" in content
        assert "MIN_PYTHON_MINOR" in content

    def test_installer_non_interactive_dry_run(self, project_root: Path, tmp_path: Path):
        """Run installer non-interactively with PYFLY_HOME pointing to tmp."""
        install_dir = tmp_path / "pyfly-test"
        env = os.environ.copy()
        env["PYFLY_HOME"] = str(install_dir)
        env["PYFLY_SOURCE"] = str(project_root)

        result = subprocess.run(
            ["bash", str(INSTALLER_PATH)],
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            stdin=subprocess.DEVNULL,  # Force non-interactive
        )
        assert result.returncode == 0, f"Installer failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

        # Verify installation artifacts
        assert (install_dir / "venv").is_dir(), "venv not created"
        assert (install_dir / "source").is_dir(), "source not copied"
        assert (install_dir / "bin" / "pyfly").exists(), "pyfly wrapper not created"
        assert os.access(install_dir / "bin" / "pyfly", os.X_OK), "pyfly wrapper not executable"

    def test_installer_wrapper_runs(self, project_root: Path, tmp_path: Path):
        """Test that the installed pyfly wrapper actually works."""
        install_dir = tmp_path / "pyfly-run-test"
        env = os.environ.copy()
        env["PYFLY_HOME"] = str(install_dir)
        env["PYFLY_SOURCE"] = str(project_root)

        # Install first
        subprocess.run(
            ["bash", str(INSTALLER_PATH)],
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            stdin=subprocess.DEVNULL,
        )

        # Now run the wrapper
        wrapper = install_dir / "bin" / "pyfly"
        result = subprocess.run(
            [str(wrapper), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Wrapper failed: {result.stderr}"
        assert "PyFly" in result.stdout
