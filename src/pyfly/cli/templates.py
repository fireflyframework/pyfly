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
"""Project templates for scaffolding."""

from __future__ import annotations

from pathlib import Path


def _to_package_name(name: str) -> str:
    """Convert project name to valid Python package name."""
    return name.replace("-", "_").replace(" ", "_").lower()


def generate_core_project(name: str, project_dir: Path) -> None:
    """Generate a core service project from template."""
    package_name = _to_package_name(name)

    # Create directory structure
    src_dir = project_dir / "src" / package_name
    tests_dir = project_dir / "tests"
    src_dir.mkdir(parents=True)
    tests_dir.mkdir(parents=True)

    # pyproject.toml
    _write(project_dir / "pyproject.toml", _CORE_PYPROJECT.format(
        name=name, package_name=package_name,
    ))

    # Source __init__.py
    _write(src_dir / "__init__.py", f'"""{ name } — PyFly Application."""\n')

    # Application entry point
    _write(src_dir / "app.py", _CORE_APP.format(
        package_name=package_name, name=name,
    ))

    # Configuration
    _write(project_dir / "pyfly.yaml", _CORE_CONFIG.format(name=name))

    # Tests
    _write(tests_dir / "__init__.py", "")
    _write(tests_dir / "conftest.py", _TEST_CONFTEST)

    # .gitignore
    _write(project_dir / ".gitignore", _GITIGNORE)


def generate_library_project(name: str, project_dir: Path) -> None:
    """Generate a library project from template."""
    package_name = _to_package_name(name)

    src_dir = project_dir / "src" / package_name
    tests_dir = project_dir / "tests"
    src_dir.mkdir(parents=True)
    tests_dir.mkdir(parents=True)

    _write(project_dir / "pyproject.toml", _LIB_PYPROJECT.format(
        name=name, package_name=package_name,
    ))

    _write(src_dir / "__init__.py", f'"""{name} — PyFly Library."""\n')

    _write(tests_dir / "__init__.py", "")
    _write(tests_dir / "conftest.py", _TEST_CONFTEST)

    _write(project_dir / ".gitignore", _GITIGNORE)


def _write(path: Path, content: str) -> None:
    """Write content to a file, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


_CORE_PYPROJECT = '''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{name}"
version = "0.1.0"
description = "{name} — built with PyFly"
requires-python = ">=3.12"
dependencies = [
    "pyfly[full]",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "ruff>=0.3",
    "mypy>=1.8",
]

[tool.hatch.build.targets.wheel]
packages = ["src/{package_name}"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --tb=short"

[tool.ruff]
target-version = "py312"
line-length = 120
'''

_CORE_APP = '''"""Application entry point."""

from pyfly.core import pyfly_application


@pyfly_application(
    name="{name}",
    scan_packages=["{package_name}"],
)
class Application:
    pass
'''

_CORE_CONFIG = '''app:
  name: {name}
  port: 8080

logging:
  level: INFO
'''

_LIB_PYPROJECT = '''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{name}"
version = "0.1.0"
description = "{name} — PyFly library"
requires-python = ">=3.12"
dependencies = [
    "pyfly",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "ruff>=0.3",
    "mypy>=1.8",
]

[tool.hatch.build.targets.wheel]
packages = ["src/{package_name}"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --tb=short"
'''

_TEST_CONFTEST = '''"""Shared test fixtures."""

import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"
'''

_GITIGNORE = '''__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.mypy_cache/
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
.venv/
.env
'''
