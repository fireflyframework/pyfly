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
"""PyFly CLI — Project scaffolding and code generation."""

from __future__ import annotations

import click

from pyfly.cli.db import db_group
from pyfly.cli.new import new_command


@click.group()
@click.version_option(package_name="pyfly")
def cli() -> None:
    """PyFly — Enterprise Python Framework CLI."""


cli.add_command(new_command, name="new")
cli.add_command(db_group, name="db")
