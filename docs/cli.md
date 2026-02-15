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
├── new.py           # pyfly new — project scaffolding (questionary TUI + Click CLI)
├── run.py           # pyfly run — application server
├── info.py          # pyfly info — environment information
├── doctor.py        # pyfly doctor — environment diagnostics
├── db.py            # pyfly db — Alembic migration management
├── templates.py     # Jinja2-based template renderer
└── templates/       # Jinja2 template files (.j2)
    ├── pyproject.toml.j2
    ├── app.py.j2
    ├── pyfly.yaml.j2
    ├── dockerfile.j2
    ├── readme.md.j2
    ├── ...
    └── hex/         # Hexagonal archetype templates
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

Create a new PyFly project with a complete directory structure, configuration files, and starter code. Supports four archetypes, selective feature inclusion, and an interactive mode.

### Usage

```bash
pyfly new <name> [OPTIONS]    # Direct mode
pyfly new [OPTIONS]           # Interactive mode (prompts for all options)
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | No | Project name. Omit to enter interactive mode. |

The project name is converted to a valid Python package name: `my-service` becomes `my_service` for the package directory.

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--archetype` | `core` | Project archetype (see below) |
| `--features` | Per archetype | Comma-separated PyFly extras (e.g. `web,data-relational,cache`) |
| `--directory` | `.` | Parent directory where the project folder will be created |

### Archetypes

| Archetype | Description | Default Features |
|-----------|-------------|-----------------|
| `core` | Minimal microservice | *(none)* |
| `web-api` | Full REST API with layered architecture | `web` |
| `hexagonal` | Hexagonal architecture (ports & adapters) | `web` |
| `library` | Reusable library package | *(none)* |

### Available Features

Features control which PyFly extras are included as dependencies and which config sections are generated:

| Feature | What it adds |
|---------|-------------|
| `web` | HTTP routing, controllers, OpenAPI |
| `data` | Repository pattern, SQLAlchemy, database config |
| `eda` | Event-driven architecture, Kafka config |
| `cache` | Redis caching, cache config |
| `client` | HTTP client (httpx) |
| `security` | JWT authentication, password encoding |
| `scheduling` | Cron-based scheduling |
| `observability` | Prometheus, OpenTelemetry |
| `cqrs` | CQRS pattern support |

### Core Archetype

The `core` archetype creates a minimal microservice with configuration and Docker support:

```
my-service/
├── pyproject.toml
├── pyfly.yaml
├── Dockerfile
├── README.md
├── .gitignore
├── .env.example
├── src/
│   └── my_service/
│       ├── __init__.py
│       └── app.py
└── tests/
    ├── __init__.py
    └── conftest.py
```

### Web API Archetype

The `web-api` archetype creates a full REST API with layered controllers, services, models, and repositories — all using PyFly stereotypes:

```
my-api/
├── pyproject.toml
├── pyfly.yaml
├── Dockerfile
├── README.md
├── .gitignore
├── .env.example
├── src/
│   └── my_api/
│       ├── __init__.py
│       ├── app.py
│       ├── controllers/
│       │   ├── health_controller.py    # @rest_controller — /health
│       │   └── item_controller.py      # @rest_controller — CRUD /items
│       ├── services/
│       │   └── item_service.py         # @service — business logic
│       ├── models/
│       │   └── item.py                 # Pydantic request/response DTOs
│       └── repositories/
│           └── item_repository.py      # @repository — in-memory store
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_item_controller.py
```

### Hexagonal Archetype

The `hexagonal` archetype creates a ports-and-adapters project with explicit domain, application, infrastructure, and API layers:

```
my-hex/
├── pyproject.toml
├── pyfly.yaml
├── Dockerfile
├── README.md
├── .gitignore
├── .env.example
├── src/
│   └── my_hex/
│       ├── __init__.py
│       ├── app.py
│       ├── domain/
│       │   ├── models.py              # Domain entities (dataclasses)
│       │   ├── events.py              # Domain events
│       │   └── ports/
│       │       ├── inbound.py         # Use-case Protocols
│       │       └── outbound.py        # Repository Protocols
│       ├── application/
│       │   └── services.py            # @service — implements inbound ports
│       ├── infrastructure/
│       │   ├── config.py              # @configuration beans
│       │   └── adapters/
│       │       └── persistence.py     # @repository — implements outbound ports
│       └── api/
│           ├── controllers.py         # @rest_controller
│           └── dto.py                 # Pydantic request/response DTOs
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── domain/
    │   └── test_models.py
    └── application/
        └── test_services.py
```

### Library Archetype

The `library` archetype creates a minimal reusable library with PEP 561 `py.typed` marker:

```
my-library/
├── pyproject.toml
├── README.md
├── .gitignore
├── src/
│   └── my_library/
│       ├── __init__.py
│       └── py.typed
└── tests/
    ├── __init__.py
    └── conftest.py
```

### Interactive Mode

When `pyfly new` is run without a `NAME` argument, it enters interactive mode with a full-featured TUI experience powered by [questionary](https://questionary.readthedocs.io/):

```
$ pyfly new

  ╭─────────────────────────────────╮
  │   PyFly Project Generator       │
  ╰─────────────────────────────────╯

  ? Project name: my-service
  ? Package name: my_service
  ? Select archetype: (use arrow keys)
    ❯ core          Minimal microservice
      web-api       Full REST API with layered architecture
      hexagonal     Hexagonal architecture (ports & adapters)
      library       Reusable library package

  ? Select features: (space to toggle, enter to confirm)
    ❯ [x] web          HTTP routing, controllers, OpenAPI
      [ ] data         Repository pattern, SQLAlchemy
      [ ] cache        Caching with Redis adapter
      [ ] security     JWT, password encoding
      [ ] eda          Event-driven architecture
      [ ] client       HTTP client (httpx)
      [ ] scheduling   Cron-based scheduling
      [ ] observability  Prometheus, OpenTelemetry
      [ ] cqrs         CQRS pattern support

  ╭─ Project Summary ───────────────╮
  │   Name:      my-service         │
  │   Package:   my_service         │
  │   Archetype: web-api            │
  │   Features:  web, data          │
  ╰─────────────────────────────────╯

  ? Create this project? Yes
```

**Features:**
- Arrow-key navigation for archetype selection (single-select)
- Space-bar toggling for feature selection (multi-select with checkbox)
- Confirmation summary with Rich-styled panel before creation
- Graceful handling of Ctrl+C (exits cleanly without traceback)

The library archetype skips the feature selection step since libraries don't include PyFly extras.

### Error Handling

If the target directory already exists, the command exits with an error. If an unknown feature is specified, the command lists valid features and exits.

### Examples

```bash
# Create a microservice (core archetype, no features)
pyfly new order-service

# Create a REST API (includes health controller, CRUD example)
pyfly new order-api --archetype web-api

# Create a hexagonal project with data and cache
pyfly new order-svc --archetype hexagonal --features web,data-relational,cache

# Create a shared library
pyfly new common-utils --archetype library

# Create in a specific directory
pyfly new payment-service --directory /projects

# Interactive mode
pyfly new
```

After creation, the CLI displays a Rich tree panel showing all created files and a hint to navigate into the project.

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
