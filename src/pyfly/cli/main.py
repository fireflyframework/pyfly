"""PyFly CLI — Project scaffolding and code generation."""

from __future__ import annotations

import click

from pyfly.cli.new import new_command


@click.group()
@click.version_option(package_name="pyfly")
def cli() -> None:
    """PyFly — Enterprise Python Framework CLI."""


cli.add_command(new_command, name="new")
