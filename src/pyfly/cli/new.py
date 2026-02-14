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
"""'pyfly new' command for scaffolding projects."""

from __future__ import annotations

from pathlib import Path

import click
from rich.panel import Panel
from rich.tree import Tree

from pyfly.cli.console import console
from pyfly.cli.templates import (
    ARCHETYPE_DESCRIPTIONS,
    AVAILABLE_FEATURES,
    DEFAULT_FEATURES,
    generate_project,
)

_ARCHETYPES = list(ARCHETYPE_DESCRIPTIONS.keys())


def _prompt_interactive() -> tuple[str, str, list[str]]:
    """Run interactive prompts when NAME is omitted."""
    console.print(Panel("[pyfly]PyFly Project Generator[/pyfly]", border_style="magenta"))

    name = click.prompt("  Project name")

    default_pkg = name.replace("-", "_").replace(" ", "_").lower()
    click.prompt("  Package name", default=default_pkg)

    # Archetype selection
    console.print("\n  [info]Archetype:[/info]")
    for i, key in enumerate(_ARCHETYPES, 1):
        desc = ARCHETYPE_DESCRIPTIONS[key]
        console.print(f"    {i}) [success]{key:12s}[/success] {desc}")

    archetype_idx = click.prompt(
        "  Select archetype",
        type=click.IntRange(1, len(_ARCHETYPES)),
        default=1,
    )
    archetype = _ARCHETYPES[archetype_idx - 1]

    # Feature selection
    defaults = DEFAULT_FEATURES[archetype]
    console.print("\n  [info]Available features:[/info]")
    for feat in AVAILABLE_FEATURES:
        marker = "x" if feat in defaults else " "
        console.print(f"    [{marker}] {feat}")

    default_str = ",".join(defaults) if defaults else ""
    features_input = click.prompt(
        "  Features (comma-separated, enter for defaults)",
        default=default_str,
    )
    features = [f.strip() for f in features_input.split(",") if f.strip()] if features_input else []

    console.print()
    return name, archetype, features


@click.command()
@click.argument("name", required=False)
@click.option(
    "--archetype",
    type=click.Choice(_ARCHETYPES),
    default=None,
    help="Project archetype.",
)
@click.option(
    "--features",
    "features_str",
    default=None,
    help="Comma-separated PyFly extras (e.g. web,data,cache).",
)
@click.option(
    "--directory",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    help="Parent directory for the new project.",
)
def new_command(name: str | None, archetype: str | None, features_str: str | None, directory: str) -> None:
    """Create a new PyFly project."""
    # Interactive mode when no name provided
    if name is None:
        name, archetype, features = _prompt_interactive()
    else:
        archetype = archetype or "core"
        if features_str is not None:
            features = [f.strip() for f in features_str.split(",") if f.strip()]
        else:
            features = list(DEFAULT_FEATURES[archetype])

    # Validate features
    invalid = set(features) - set(AVAILABLE_FEATURES)
    if invalid:
        console.print(f"[error]Unknown features: {', '.join(sorted(invalid))}[/error]")
        console.print(f"[dim]Available: {', '.join(AVAILABLE_FEATURES)}[/dim]")
        raise SystemExit(1)

    parent = Path(directory)
    project_dir = parent / name

    if project_dir.exists():
        console.print(f"[error]Directory '{project_dir}' already exists.[/error]")
        raise SystemExit(1)

    generate_project(name, project_dir, archetype, features)

    # Build a tree showing created structure
    tree = Tree(f"[success]{name}/[/success]")
    for path in sorted(project_dir.rglob("*")):
        if path.is_file():
            relative = path.relative_to(project_dir)
            tree.add(f"[dim]{relative}[/dim]")

    panel = Panel(
        tree,
        title=f"[success]Created {archetype} project[/success]",
        border_style="green",
    )
    console.print(panel)
    console.print(f"\n  [info]cd {project_dir}[/info] to get started!\n")
