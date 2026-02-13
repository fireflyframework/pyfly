"""'pyfly new' command for scaffolding projects."""

from __future__ import annotations

from pathlib import Path

import click

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
        raise click.ClickException(f"Directory '{project_dir}' already exists.")

    if archetype == "library":
        generate_library_project(name, project_dir)
    else:
        generate_core_project(name, project_dir)

    click.echo(f"Created {archetype} project: {project_dir}")
