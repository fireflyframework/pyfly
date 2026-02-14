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
"""'pyfly db' commands for Alembic migration management."""

from __future__ import annotations

from pathlib import Path

import click
from alembic import command
from alembic.config import Config

_ENV_PY_TEMPLATE = '''\
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from pyfly.data import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Helper executed inside an async connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


import asyncio

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
'''


def _get_alembic_config() -> Config:
    """Load Alembic config from the current directory.

    Raises :class:`click.ClickException` when ``alembic.ini`` is missing.
    """
    ini_path = Path("alembic.ini")
    if not ini_path.exists():
        raise click.ClickException(
            "alembic.ini not found. Run 'pyfly db init' first."
        )
    return Config(str(ini_path))


@click.group()
def db_group() -> None:
    """Database migration commands (powered by Alembic)."""


@db_group.command("init")
def init_cmd() -> None:
    """Initialize the Alembic migration environment."""
    directory = "alembic"
    if Path(directory).exists():
        raise click.ClickException(
            f"Directory '{directory}' already exists. "
            "Remove it first if you want to re-initialize."
        )

    cfg = Config("alembic.ini")
    command.init(cfg, directory)

    # Overwrite the generated env.py with the PyFly-customized template.
    env_py_path = Path(directory) / "env.py"
    env_py_path.write_text(_ENV_PY_TEMPLATE)

    click.echo("Initialized Alembic migration environment in 'alembic/'.")


@db_group.command("migrate")
@click.option(
    "--message",
    "-m",
    default=None,
    help="Revision message.",
)
def migrate_cmd(message: str | None) -> None:
    """Auto-generate a new migration revision."""
    cfg = _get_alembic_config()
    command.revision(cfg, message=message, autogenerate=True)
    click.echo("Migration revision created.")


@db_group.command("upgrade")
@click.argument("revision", default="head")
def upgrade_cmd(revision: str) -> None:
    """Upgrade the database to a given revision (default: head)."""
    cfg = _get_alembic_config()
    command.upgrade(cfg, revision)
    click.echo(f"Database upgraded to {revision}.")


@db_group.command("downgrade")
@click.argument("revision")
def downgrade_cmd(revision: str) -> None:
    """Downgrade the database to a given revision."""
    cfg = _get_alembic_config()
    command.downgrade(cfg, revision)
    click.echo(f"Database downgraded to {revision}.")
