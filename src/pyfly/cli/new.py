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
from pyfly.cli.templates import generate_core_project, generate_library_project


@click.command()
@click.argument("name")
@click.option(
    "--archetype",
    type=click.Choice(["core", "library"]),
    default="core",
    help="Project archetype (core service or library).",
)
@click.option(
    "--directory",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    help="Parent directory for the new project.",
)
def new_command(name: str, archetype: str, directory: str) -> None:
    """Create a new PyFly project."""
    parent = Path(directory)
    project_dir = parent / name

    if project_dir.exists():
        console.print(f"[error]Directory '{project_dir}' already exists.[/error]")
        raise SystemExit(1)

    if archetype == "library":
        generate_library_project(name, project_dir)
    else:
        generate_core_project(name, project_dir)

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
