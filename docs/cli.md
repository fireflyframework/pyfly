# CLI Reference

The PyFly CLI provides command-line tools for project scaffolding, application management, database migrations, environment diagnostics, and framework information.

**Install:** `pip install -e ".[cli]"` (requires Click, Rich, Jinja2)

**Entry point:** `pyfly` (registered as a console script via `pyproject.toml`)

---

## Table of Contents

- [Overview](#overview)
- [Global Options](#global-options)
- [pyfly new](#pyfly-new)
- [pyfly run](#pyfly-run)
- [pyfly info](#pyfly-info)
- [pyfly doctor](#pyfly-doctor)
- [pyfly db](#pyfly-db)
  - [pyfly db init](#pyfly-db-init)
  - [pyfly db migrate](#pyfly-db-migrate)
  - [pyfly db upgrade](#pyfly-db-upgrade)
  - [pyfly db downgrade](#pyfly-db-downgrade)
- [Development Workflow](#typical-development-workflow)

---

## Overview

The CLI is built with [Click](https://click.palletsprojects.com/) for command parsing and [Rich](https://rich.readthedocs.io/) for beautiful terminal output. When you run `pyfly --help`, you'll see an ASCII banner followed by the command listing.

All commands are organized as a Click group under the `pyfly` entry point:

```
pyfly
├── new       — Create a new project
├── run       — Start the application server
├── info      — Display framework information
├── doctor    — Diagnose environment
└── db        — Database migration commands
    ├── init      — Initialize Alembic
    ├── migrate   — Generate migration
    ├── upgrade   — Apply migrations
    └── downgrade — Revert migrations
```

### Architecture

The CLI module follows the same patterns as the rest of PyFly:

```
src/pyfly/cli/
├── __init__.py
├── main.py          # PyFlyCLI group, command registration
├── console.py       # Shared Rich console, theme, print_banner()
├── new.py           # pyfly new — project scaffolding
├── run.py           # pyfly run — application server
├── info.py          # pyfly info — environment information
├── doctor.py        # pyfly doctor — environment diagnostics
├── db.py            # pyfly db — Alembic migration management
└── templates.py     # Project template generators
```

### Rich Console Theme

The CLI uses a custom Rich theme for consistent, colored output across all commands:

| Style | Color | Usage |
|-------|-------|-------|
| `info` | Cyan | Informational messages, labels |
| `success` | Bold green | Success indicators (checkmarks) |
| `warning` | Bold yellow | Warnings (non-fatal issues) |
| `error` | Bold red | Errors (fatal issues) |
| `pyfly` | Bold magenta | PyFly branding elements |

All commands share a single `console` instance from `pyfly.cli.console`, ensuring consistent styling. The `print_banner()` function renders the PyFly ASCII art banner.

---

## Global Options

```bash
pyfly --version    # Show PyFly version (from pyproject.toml)
pyfly --help       # Show help with ASCII banner and all commands
```

The `--version` flag reads the version from the `pyfly` package metadata.

---

## pyfly new

Create a new PyFly project with a complete directory structure, configuration files, and starter code.

### Usage

```bash
pyfly new <name> [OPTIONS]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | Yes | Project name (used for directory and Python package name) |

The project name is converted to a valid Python package name: `my-service` becomes `my_service` for the package directory.

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--archetype` | `core` | Project template: `core` (microservice) or `library` (shared library) |
| `--directory` | `.` | Parent directory where the project folder will be created |

### Core Archetype

The `core` archetype creates a full microservice project ready to run:

```
my-service/
├── pyproject.toml          # Project metadata, PyFly dependency
├── pyfly.yaml              # Framework configuration
├── src/
│   └── my_service/
│       ├── __init__.py
│       └── app.py          # Application entry point
└── tests/
    └── __init__.py
```

**Generated `app.py`:**
```python
from pyfly.core import pyfly_application, PyFlyApplication

@pyfly_application(
    name="my-service",
    version="0.1.0",
    scan_packages=["my_service"],
)
class Application:
    pass
```

**Generated `pyfly.yaml`:**
```yaml
pyfly:
  app:
    name: my-service
    version: 0.1.0
  web:
    port: 8080
    docs:
      enabled: true
  logging:
    level:
      root: INFO
```

### Library Archetype

The `library` archetype creates a minimal shared library project (no web server, no framework config):

```
my-library/
├── pyproject.toml
├── src/
│   └── my_library/
│       └── __init__.py
└── tests/
    └── __init__.py
```

### Error Handling

If the target directory already exists, the command exits with an error message rather than overwriting.

### Examples

```bash
# Create a microservice
pyfly new order-service

# Create a shared library
pyfly new common-utils --archetype library

# Create in a specific directory
pyfly new payment-service --directory /projects
```

After creation, the CLI displays a Rich tree panel showing all created files and a hint to navigate into the project:

```
╭─ Created core project ──────────╮
│ 📁 order-service/               │
│ ├── pyfly.yaml                  │
│ ├── pyproject.toml              │
│ ├── src/order_service/__init__.py│
│ ├── src/order_service/app.py    │
│ └── tests/__init__.py           │
╰─────────────────────────────────╯

  cd order-service to get started!
```

---

## pyfly run

Start the PyFly application using [uvicorn](https://www.uvicorn.org/) as the ASGI server.

### Usage

```bash
pyfly run [OPTIONS]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `8080` | Port number |
| `--reload` | `false` | Enable auto-reload on code changes (for development) |
| `--app` | Auto-discovered | Application import path (e.g., `myapp.app:Application`) |

### Application Discovery

When `--app` is not provided, `pyfly run` attempts to discover the application automatically:

1. Looks for `pyfly.yaml` in the current directory
2. Reads the `app.module` key for the import path

```yaml
# pyfly.yaml
app:
  module: my_service.app:Application
```

If neither `--app` nor a discoverable config file is found, the command exits with a clear error:

```
✗ No application found.
  Provide --app flag or create a pyfly.yaml in the current directory.
```

### Startup Output

When the server starts, the CLI displays connection details:

```
Starting PyFly application...
  App:    my_service.app:Application
  Host:   0.0.0.0:8080
  Reload: on
```

### Requirements

Requires `uvicorn` to be installed. If not available, the command suggests installing the `web` extra:

```
✗ uvicorn is not installed.
  Install it with: pip install 'pyfly[web]'
```

### Examples

```bash
# Development with auto-reload
pyfly run --reload

# Custom port
pyfly run --port 3000

# Explicit app path
pyfly run --app my_service.app:Application

# Production binding
pyfly run --host 0.0.0.0 --port 80
```

---

## pyfly info

Display comprehensive information about the PyFly installation and environment.

### Usage

```bash
pyfly info
```

### Output

The command displays two Rich tables:

**1. Environment Table**

| Field | Example |
|-------|---------|
| Python | 3.12.5 |
| Platform | macOS-14.5-arm64 |
| Architecture | arm64 |

**2. Installed Extras Table**

Shows the installation status of each optional module by attempting to import the underlying library:

| Extra | Detection Module | What It Provides |
|-------|-----------------|------------------|
| `web` | `starlette` | HTTP server, routing, middleware |
| `data` | `sqlalchemy` | Database access, repositories |
| `eda` | `aiokafka` | Event-driven architecture |
| `kafka` | `aiokafka` | Apache Kafka messaging |
| `rabbitmq` | `aio_pika` | RabbitMQ messaging |
| `redis` | `redis` | Redis client |
| `cache` | `redis` | Caching with Redis |
| `client` | `httpx` | HTTP client with retry |
| `observability` | `prometheus_client` | Metrics, tracing, logging |
| `security` | `jwt` | JWT authentication |
| `scheduling` | `croniter` | Cron scheduling |
| `cli` | `rich` | CLI tools |

Each extra shows as either `✓ installed` (green) or `not installed` (dimmed).

This is useful for verifying which framework modules are available after installation, especially when using selective extras rather than `full`.

---

## pyfly doctor

Run a comprehensive health check on your development environment, verifying Python version, tools, and PyFly installation.

### Usage

```bash
pyfly doctor
```

### Checks Performed

**1. Python Version**

Verifies Python >= 3.12. Displays the exact version with a pass/fail indicator.

```
✓ Python 3.12.5          # Pass
✗ Python 3.11.2 (requires >=3.12)  # Fail
```

**2. Virtual Environment**

Checks if a virtual environment is active by comparing `sys.prefix` to `sys.base_prefix`. Shows a warning if not in a venv — this is non-fatal but recommended.

```
✓ Virtual environment active    # In venv
! No virtual environment detected  # Warning
```

**3. Required Tools**

Checks that essential tools are available on PATH using `shutil.which()`:

| Tool | Purpose | Impact if Missing |
|------|---------|-------------------|
| `git` | Version control | Overall check fails |
| `pip` | Package manager | Overall check fails |

**4. Optional Tools**

Checks for recommended development tools:

| Tool | Purpose | Impact if Missing |
|------|---------|-------------------|
| `uvicorn` | ASGI server (`pyfly run`) | Informational only |
| `alembic` | Database migrations (`pyfly db`) | Informational only |
| `ruff` | Linter & formatter | Informational only |
| `mypy` | Type checker | Informational only |

**5. PyFly Installation**

Verifies that PyFly itself is importable and displays the installed version:

```
✓ pyfly v0.1.0
```

### Summary

The doctor command ends with a clear summary:
- **All checks passed!** (green) — Environment is ready
- **Some issues found. See above for details.** (yellow) — Action needed

---

## pyfly db

Database migration commands powered by [Alembic](https://alembic.sqlalchemy.org/). These commands wrap Alembic's functionality with PyFly-specific defaults and Rich output.

All `pyfly db` subcommands expect `alembic.ini` to exist in the current directory (created by `pyfly db init`).

### pyfly db init

Initialize the Alembic migration environment in the current directory.

```bash
pyfly db init
```

**What it does:**

1. Creates an `alembic/` directory with Alembic's standard structure
2. Creates `alembic.ini` configuration file
3. **Overwrites `alembic/env.py`** with a PyFly-customized template that includes:
   - `async_engine_from_config` for async database support (asyncpg, aiosqlite)
   - `Base.metadata` from `pyfly.data` as the target metadata for autogeneration
   - Support for both offline (SQL script) and online (async connection) migration modes

**Error handling:** If an `alembic/` directory already exists, the command exits with an error rather than overwriting.

```
✗ Directory 'alembic' already exists. Remove it first if you want to re-initialize.
```

### pyfly db migrate

Auto-generate a new migration revision by comparing your SQLAlchemy models to the current database state.

```bash
pyfly db migrate [-m "description"]
```

| Option | Description |
|--------|-------------|
| `-m`, `--message` | Revision message describing the changes |

**Examples:**
```bash
pyfly db migrate -m "add user table"
pyfly db migrate -m "add order status column"
```

This runs Alembic's `revision --autogenerate`, which:
1. Compares your current `Base.metadata` (all entity models) with the database
2. Generates upgrade/downgrade functions in a new version file under `alembic/versions/`

**Prerequisites:** `alembic.ini` must exist (run `pyfly db init` first).

### pyfly db upgrade

Apply pending migrations to bring the database up to a specific revision.

```bash
pyfly db upgrade [REVISION]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `revision` | `head` | Target revision (use `head` for latest) |

**Examples:**
```bash
pyfly db upgrade           # Apply all pending migrations
pyfly db upgrade head      # Same as above (explicit)
pyfly db upgrade abc123    # Upgrade to specific revision
```

### pyfly db downgrade

Revert the database to a previous revision.

```bash
pyfly db downgrade REVISION
```

| Argument | Required | Description |
|----------|----------|-------------|
| `revision` | Yes | Target revision to downgrade to |

**Examples:**
```bash
pyfly db downgrade -1       # Revert one migration step
pyfly db downgrade abc123   # Revert to specific revision
pyfly db downgrade base     # Revert all migrations
```

---

## Typical Development Workflow

Here's a typical workflow using the CLI tools throughout the lifecycle of a PyFly project:

```bash
# 1. Check your environment is ready
pyfly doctor

# 2. Create a new project
pyfly new order-service
cd order-service

# 3. Verify framework info and installed extras
pyfly info

# 4. Initialize database migrations
pyfly db init

# 5. Create initial migration from your entity models
pyfly db migrate -m "initial schema"

# 6. Apply the migration
pyfly db upgrade

# 7. Start developing with auto-reload
pyfly run --reload

# 8. As you add/modify entities, generate new migrations
pyfly db migrate -m "add order status"
pyfly db upgrade

# 9. If you need to roll back a migration
pyfly db downgrade -1
```

---

## Extending the CLI

The CLI is built on Click, making it straightforward to add custom commands for your project. The entry point is defined in `pyproject.toml`:

```toml
[project.scripts]
pyfly = "pyfly.cli.main:cli"
```

To add custom commands, create a Click command and register it with the CLI group:

```python
import click
from pyfly.cli.main import cli

@click.command()
@click.argument("entity_name")
def generate_command(entity_name: str) -> None:
    """Generate boilerplate for a new entity."""
    click.echo(f"Generating {entity_name} entity, repository, and service...")

cli.add_command(generate_command, name="generate")
```
