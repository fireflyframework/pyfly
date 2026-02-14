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
"""Jinja2-based project template renderer for scaffolding."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, PackageLoader

# Available features that map to PyFly extras
AVAILABLE_FEATURES: list[str] = [
    "web", "data", "eda", "cache", "client",
    "security", "scheduling", "observability", "cqrs",
]

# Default features per archetype
DEFAULT_FEATURES: dict[str, list[str]] = {
    "core": [],
    "web-api": ["web"],
    "hexagonal": ["web"],
    "library": [],
}

# Archetype descriptions for interactive mode
ARCHETYPE_DESCRIPTIONS: dict[str, str] = {
    "core": "Minimal microservice",
    "web-api": "Full REST API with layered architecture",
    "hexagonal": "Hexagonal architecture (ports & adapters)",
    "library": "Reusable library package",
}

# Template → output path mapping per archetype.
# Output paths use {package_name} as a placeholder.
_ARCHETYPE_FILES: dict[str, list[tuple[str, str]]] = {
    "core": [
        ("pyproject.toml.j2", "pyproject.toml"),
        ("app.py.j2", "src/{package_name}/app.py"),
        ("init.py.j2", "src/{package_name}/__init__.py"),
        ("pyfly.yaml.j2", "pyfly.yaml"),
        ("conftest.py.j2", "tests/conftest.py"),
        ("init_empty.j2", "tests/__init__.py"),
        ("gitignore.j2", ".gitignore"),
        ("readme.md.j2", "README.md"),
        ("dockerfile.j2", "Dockerfile"),
        ("env.example.j2", ".env.example"),
    ],
    "web-api": [
        ("pyproject.toml.j2", "pyproject.toml"),
        ("app.py.j2", "src/{package_name}/app.py"),
        ("init.py.j2", "src/{package_name}/__init__.py"),
        ("pyfly.yaml.j2", "pyfly.yaml"),
        ("conftest.py.j2", "tests/conftest.py"),
        ("init_empty.j2", "tests/__init__.py"),
        ("gitignore.j2", ".gitignore"),
        ("readme.md.j2", "README.md"),
        ("dockerfile.j2", "Dockerfile"),
        ("env.example.j2", ".env.example"),
        # Controllers
        ("init_empty.j2", "src/{package_name}/controllers/__init__.py"),
        ("health_controller.py.j2", "src/{package_name}/controllers/health_controller.py"),
        ("item_controller.py.j2", "src/{package_name}/controllers/item_controller.py"),
        # Services
        ("init_empty.j2", "src/{package_name}/services/__init__.py"),
        ("item_service.py.j2", "src/{package_name}/services/item_service.py"),
        # Models
        ("init_empty.j2", "src/{package_name}/models/__init__.py"),
        ("item_model.py.j2", "src/{package_name}/models/item.py"),
        # Repositories
        ("init_empty.j2", "src/{package_name}/repositories/__init__.py"),
        ("item_repository.py.j2", "src/{package_name}/repositories/item_repository.py"),
        # Tests
        ("test_item_controller.py.j2", "tests/test_item_controller.py"),
    ],
    "hexagonal": [
        ("pyproject.toml.j2", "pyproject.toml"),
        ("app.py.j2", "src/{package_name}/app.py"),
        ("init.py.j2", "src/{package_name}/__init__.py"),
        ("pyfly.yaml.j2", "pyfly.yaml"),
        ("conftest.py.j2", "tests/conftest.py"),
        ("init_empty.j2", "tests/__init__.py"),
        ("gitignore.j2", ".gitignore"),
        ("readme.md.j2", "README.md"),
        ("dockerfile.j2", "Dockerfile"),
        ("env.example.j2", ".env.example"),
        # Domain layer
        ("init_empty.j2", "src/{package_name}/domain/__init__.py"),
        ("hex/domain_models.py.j2", "src/{package_name}/domain/models.py"),
        ("hex/domain_events.py.j2", "src/{package_name}/domain/events.py"),
        ("init_empty.j2", "src/{package_name}/domain/ports/__init__.py"),
        ("hex/ports_inbound.py.j2", "src/{package_name}/domain/ports/inbound.py"),
        ("hex/ports_outbound.py.j2", "src/{package_name}/domain/ports/outbound.py"),
        # Application layer
        ("init_empty.j2", "src/{package_name}/application/__init__.py"),
        ("hex/app_services.py.j2", "src/{package_name}/application/services.py"),
        # Infrastructure layer
        ("init_empty.j2", "src/{package_name}/infrastructure/__init__.py"),
        ("init_empty.j2", "src/{package_name}/infrastructure/adapters/__init__.py"),
        ("hex/persistence.py.j2", "src/{package_name}/infrastructure/adapters/persistence.py"),
        ("hex/config.py.j2", "src/{package_name}/infrastructure/config.py"),
        # API layer
        ("init_empty.j2", "src/{package_name}/api/__init__.py"),
        ("hex/controllers.py.j2", "src/{package_name}/api/controllers.py"),
        ("hex/dto.py.j2", "src/{package_name}/api/dto.py"),
        # Tests
        ("init_empty.j2", "tests/domain/__init__.py"),
        ("hex/test_models.py.j2", "tests/domain/test_models.py"),
        ("init_empty.j2", "tests/application/__init__.py"),
        ("hex/test_services.py.j2", "tests/application/test_services.py"),
    ],
    "library": [
        ("pyproject.toml.j2", "pyproject.toml"),
        ("init.py.j2", "src/{package_name}/__init__.py"),
        ("init_empty.j2", "tests/__init__.py"),
        ("conftest.py.j2", "tests/conftest.py"),
        ("gitignore.j2", ".gitignore"),
        ("readme.md.j2", "README.md"),
        ("py.typed.j2", "src/{package_name}/py.typed"),
    ],
}


def _to_package_name(name: str) -> str:
    """Convert project name to valid Python package name."""
    return name.replace("-", "_").replace(" ", "_").lower()


def _write(path: Path, content: str) -> None:
    """Write content to a file, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _build_context(name: str, archetype: str, features: list[str]) -> dict[str, object]:
    """Build the Jinja2 template context."""
    package_name = _to_package_name(name)
    return {
        "name": name,
        "package_name": package_name,
        "archetype": archetype,
        "features": features,
        "has_web": "web" in features,
        "has_data": "data" in features,
        "has_eda": "eda" in features,
        "has_cache": "cache" in features,
        "has_client": "client" in features,
        "has_security": "security" in features,
        "has_scheduling": "scheduling" in features,
        "has_observability": "observability" in features,
        "has_cqrs": "cqrs" in features,
    }


def _get_env() -> Environment:
    """Create the Jinja2 template environment."""
    return Environment(
        loader=PackageLoader("pyfly.cli", "templates"),
        keep_trailing_newline=True,
        lstrip_blocks=True,
        trim_blocks=True,
    )


def generate_project(name: str, project_dir: Path, archetype: str, features: list[str]) -> None:
    """Generate a project from Jinja2 templates.

    Args:
        name: Project name (e.g. ``"my-service"``).
        project_dir: Target directory to create.
        archetype: One of ``core``, ``web-api``, ``hexagonal``, ``library``.
        features: Selected PyFly extras (e.g. ``["web", "data"]``).
    """
    env = _get_env()
    context = _build_context(name, archetype, features)
    package_name = _to_package_name(name)

    for template_name, output_path in _ARCHETYPE_FILES[archetype]:
        output_path = output_path.replace("{package_name}", package_name)
        rendered = env.get_template(template_name).render(context)
        _write(project_dir / output_path, rendered)


# Backward-compatible convenience functions
def generate_core_project(name: str, project_dir: Path) -> None:
    """Generate a core service project."""
    generate_project(name, project_dir, "core", DEFAULT_FEATURES["core"])


def generate_library_project(name: str, project_dir: Path) -> None:
    """Generate a library project."""
    generate_project(name, project_dir, "library", DEFAULT_FEATURES["library"])
