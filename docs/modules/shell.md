# Shell Guide

PyFly's shell module provides a Spring Shell-inspired CLI application framework
with full dependency injection integration. Decorate methods with `@shell_method`
inside `@shell_component` classes, and PyFly automatically registers them as CLI
commands, infers parameters from type hints, and wires everything through the DI
container at startup. The module also supports `CommandLineRunner` and
`ApplicationRunner` protocols for one-shot post-startup tasks.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Concepts](#core-concepts)
   - [@shell_component](#shell_component)
   - [@shell_method](#shell_method)
   - [@shell_option and @shell_argument](#shell_option-and-shell_argument)
3. [Parameter Inference](#parameter-inference)
4. [ShellRunnerPort Protocol](#shellrunnerport-protocol)
5. [CommandLineRunner and ApplicationRunner](#commandlinerunner-and-applicationrunner)
6. [ApplicationArguments](#applicationarguments)
7. [Auto-Configuration](#auto-configuration)
8. [Configuration Reference](#configuration-reference)
9. [Complete Example: Database Migration CLI](#complete-example-database-migration-cli)
10. [Testing](#testing)
11. [See Also](#see-also)

---

## Architecture Overview

```
@shell_component classes (your code)
          |
          v
    @shell_method methods
          |  (infer_params extracts ShellParam descriptors from type hints)
          v
    ShellRunnerPort  (protocol / port)
          |
          +-- ClickShellAdapter   (Click library — default)
          +-- (Future: Typer, etc.)
          |
          v
    ApplicationContext wires everything at startup
```

Your CLI commands live in `@shell_component` classes that participate in DI like
any other stereotype. The `ApplicationContext` scans these classes at startup,
finds all `@shell_method` methods, infers CLI parameters from type hints, and
registers them with the `ShellRunnerPort` adapter.

---

## Core Concepts

### @shell_component

Marks a class as a DI-managed shell component. It behaves like `@component` but
signals that the class contains CLI command methods:

```python
from pyfly.shell import shell_component, shell_method

@shell_component
class GreetingCommands:
    def __init__(self, greeting_service: GreetingService) -> None:
        self._service = greeting_service

    @shell_method(help="Say hello to someone")
    def greet(self, name: str) -> str:
        return self._service.greet(name)
```

The DI container resolves `GreetingService` automatically — shell components
have full access to constructor injection, `Autowired()` fields, and all other
DI features.

### @shell_method

Marks a method as a CLI command. The method is registered with the shell adapter
using an auto-derived command name (underscores become hyphens) or an explicit
`key`:

```python
@shell_method(key="say-hello", help="Greet a user", group="greetings")
def say_hello(self, name: str, loud: bool = False) -> str:
    msg = f"Hello, {name}!"
    return msg.upper() if loud else msg
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `key` | `str` | method name (kebab-case) | The command name in the CLI |
| `help` | `str` | `""` | Help text for the command |
| `group` | `str` | `""` | Command group for organised help output |

### @shell_option and @shell_argument

Override inferred parameter metadata when you need explicit control:

```python
from pyfly.shell import shell_method, shell_option, shell_argument

@shell_method()
@shell_option("--verbose", is_flag=True, help="Enable verbose output")
@shell_argument("service", help="Service to deploy")
def deploy(service: str, verbose: bool = False) -> str:
    return f"Deploying {service}{'(verbose)' if verbose else ''}"
```

**@shell_option parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Option name (e.g. `--verbose`) |
| `type` | `type \| None` | `None` | Value type (`None` = infer from signature) |
| `is_flag` | `bool` | `False` | Boolean flag (no value expected) |
| `help` | `str` | `""` | Help text |
| `default` | `Any` | `None` | Default value |

**@shell_argument parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Argument name |
| `type` | `type \| None` | `None` | Value type (`None` = infer from signature) |
| `help` | `str` | `""` | Help text |
| `required` | `bool` | `True` | Whether the argument must be supplied |
| `default` | `Any` | `None` | Default value |

---

## Parameter Inference

PyFly automatically infers CLI parameters from your method's type hints using
`infer_params()`. The rules are:

| Signature Pattern | CLI Mapping | Example |
|-------------------|-------------|---------|
| `name: str` (no default) | Positional argument | `greet Alice` |
| `count: int = 3` (has default) | `--count` option | `greet --count 5` |
| `verbose: bool = False` | `--verbose` flag | `greet --verbose` |
| `query: str \| None = None` | `--query` option (optional) | `search --query foo` |

Explicit `@shell_option` / `@shell_argument` decorators are merged on top of the
inferred defaults, so you only need them when you want to add help text, override
a default, or change the inferred kind.

---

## ShellRunnerPort Protocol

The port contract that any shell adapter must implement:

```python
from pyfly.shell import ShellRunnerPort

class ShellRunnerPort(Protocol):
    def register_command(
        self,
        key: str,
        handler: Callable[..., Any],
        *,
        help_text: str = "",
        group: str = "",
        params: list[ShellParam] | None = None,
    ) -> None: ...

    async def run(self, args: list[str] | None = None) -> int: ...

    async def run_interactive(self) -> None: ...
```

| Method | Description |
|--------|-------------|
| `register_command()` | Register a command with its handler, parameters, and metadata |
| `run()` | Execute the shell with the given arguments, return exit code |
| `run_interactive()` | Start an interactive REPL loop |

---

## CommandLineRunner and ApplicationRunner

These protocols provide post-startup hooks — beans that implement them are
invoked automatically after the `ApplicationContext` has fully started. This
mirrors Spring Boot's `CommandLineRunner` and `ApplicationRunner`:

```python
from pyfly.shell import CommandLineRunner, ApplicationRunner, ApplicationArguments

@service
class DbMigrator:
    """Runs database migrations on startup."""

    async def run(self, args: list[str]) -> None:
        if "--migrate" in args:
            await self._apply_migrations()
```

- **`CommandLineRunner`** — Receives raw `list[str]` arguments
- **`ApplicationRunner`** — Receives parsed `ApplicationArguments`

Runners are invoked in `@order` priority (lowest first). The `ApplicationContext`
distinguishes runners from `ShellRunnerPort` instances to prevent structural
typing false matches.

---

## ApplicationArguments

A parsed representation of command-line arguments that separates option args
(`--key=value`, `--flag`) from non-option args:

```python
from pyfly.shell import ApplicationArguments

args = ApplicationArguments.from_args(["serve", "--port=8080", "--debug"])

args.source_args      # ["serve", "--port=8080", "--debug"]
args.option_args      # ["--port=8080", "--debug"]
args.non_option_args  # ["serve"]

args.contains_option("port")       # True
args.get_option_values("port")     # ["8080"]
args.contains_option("verbose")    # False
```

---

## Auto-Configuration

Shell auto-configuration is activated when `pyfly.shell.enabled` is set to
`true` and no user-provided `ShellRunnerPort` bean exists:

```yaml
# pyfly.yaml
pyfly:
  shell:
    enabled: true
```

The `ShellAutoConfiguration` class registers a `ClickShellAdapter` as the
default `ShellRunnerPort`:

| Condition | Bean | Type |
|-----------|------|------|
| `pyfly.shell.enabled=true` + no existing `ShellRunnerPort` | `shell_runner` | `ClickShellAdapter` |

You can override by registering your own `ShellRunnerPort` bean:

```python
@configuration
class MyShellConfig:
    @bean
    def shell_runner(self) -> ShellRunnerPort:
        return MyCustomShellAdapter()
```

---

## Configuration Reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `pyfly.shell.enabled` | `bool` | `false` | Enable the shell subsystem and auto-configuration |

---

## Complete Example: Database Migration CLI

```python
from pyfly.container import service
from pyfly.shell import shell_component, shell_method, shell_option

@service
class MigrationService:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def migrate(self, target: str = "head") -> str:
        # Run Alembic migrations...
        return f"Migrated to {target}"

    async def rollback(self, steps: int = 1) -> str:
        return f"Rolled back {steps} step(s)"


@shell_component
class DbCommands:
    def __init__(self, migrations: MigrationService) -> None:
        self._migrations = migrations

    @shell_method(group="db", help="Apply database migrations")
    @shell_option("--target", help="Migration target revision")
    async def migrate(self, target: str = "head") -> str:
        return await self._migrations.migrate(target)

    @shell_method(group="db", help="Rollback database migrations")
    async def rollback(self, steps: int = 1) -> str:
        return await self._migrations.rollback(steps)
```

Running the application:

```bash
# Single command execution
python -m myapp db migrate --target head

# Interactive REPL
python -m myapp --interactive
> db migrate
Migrated to head
> db rollback --steps 2
Rolled back 2 step(s)
```

---

## Testing

Shell commands are ordinary methods on DI-managed classes — test them directly
or through the `ClickShellAdapter`:

```python
from pyfly.shell import ShellParam
from pyfly.shell.adapters.click_adapter import ClickShellAdapter


def test_greet_command():
    adapter = ClickShellAdapter()
    captured = {}

    def greet(name: str) -> None:
        captured["name"] = name

    adapter.register_command(
        "greet",
        greet,
        params=[ShellParam(name="name", param_type=str, is_option=False)],
    )
    exit_code, output = adapter.invoke(["greet", "Alice"])
    assert exit_code == 0
    assert captured["name"] == "Alice"
```

For integration tests with the full `ApplicationContext`:

```python
import pytest
from pyfly.context.application_context import ApplicationContext
from pyfly.core.config import Config
from pyfly.shell import ShellRunnerPort


@pytest.mark.asyncio
async def test_shell_wiring():
    config = Config({"pyfly": {"shell": {"enabled": True}}})
    ctx = ApplicationContext(config)
    await ctx.start()
    try:
        runner = ctx.get_bean(ShellRunnerPort)
        assert runner is not None
    finally:
        await ctx.stop()
```

---

## See Also

- [Click Adapter](../adapters/click.md) — Adapter-specific features and configuration
- [Dependency Injection Guide](dependency-injection.md) — Constructor injection and stereotypes
- [Core & Lifecycle Guide](core.md) — Application startup sequence
- Spring Shell documentation — The Java equivalent that inspired this module
