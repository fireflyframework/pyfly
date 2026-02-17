# Click Adapter

> **Module:** Shell — [Module Guide](../modules/shell.md)
> **Package:** `pyfly.shell.adapters.click_adapter`
> **Backend:** Click 8.1+

## Quick Start

### Installation

```bash
pip install pyfly[shell]
```

### Minimal Configuration

```yaml
# pyfly.yaml
pyfly:
  shell:
    enabled: true
```

### Minimal Example

```python
from pyfly.shell import shell_component, shell_method

@shell_component
class MyCommands:
    @shell_method(help="Say hello")
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"
```

---

## Configuration Reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `pyfly.shell.enabled` | `bool` | `false` | Enable shell auto-configuration |

---

## Adapter-Specific Features

### ClickShellAdapter

Implements `ShellRunnerPort` using `click.Group` as the root command.

- **Constructor params:** `name` (app name), `help_text` (root help string)
- **Grouped commands:** Commands with a `group` parameter are nested under `click.Group` sub-commands (e.g. `db migrate`, `db rollback`)
- **Async handlers:** Async command handlers are automatically wrapped — `asyncio.run()` is used when no event loop is running, `ThreadPoolExecutor` fallback when inside a running loop

### Parameter Mapping

Python types are mapped to Click parameter types:

| Python Type | Click Type |
|-------------|------------|
| `str` | `click.STRING` |
| `int` | `click.INT` |
| `float` | `click.FLOAT` |
| `bool` | `click.BOOL` |

### Command Registration

The `ApplicationContext` automatically registers `@shell_method` methods from
`@shell_component` beans during startup. You can also register commands manually:

```python
from pyfly.shell import ShellParam
from pyfly.shell.adapters.click_adapter import ClickShellAdapter

adapter = ClickShellAdapter(name="myapp", help_text="My CLI app")
adapter.register_command(
    "deploy",
    deploy_handler,
    help_text="Deploy a service",
    group="ops",
    params=[
        ShellParam(name="service", param_type=str, is_option=False),
        ShellParam(name="env", param_type=str, is_option=True, default="staging"),
    ],
)
```

### Invocation Modes

| Method | Description |
|--------|-------------|
| `invoke(args)` | Synchronous invocation returning `(exit_code, output)` |
| `run(args)` | Async invocation returning exit code |
| `run_interactive()` | Simple REPL loop — reads lines, splits tokens, dispatches |

---

## Testing

Test commands through the adapter without starting the full application:

```python
from pyfly.shell.adapters.click_adapter import ClickShellAdapter
from pyfly.shell import ShellParam

adapter = ClickShellAdapter()

def greet(name: str) -> None:
    print(f"Hello, {name}!")

adapter.register_command(
    "greet", greet,
    params=[ShellParam(name="name", param_type=str, is_option=False)],
)

exit_code, output = adapter.invoke(["greet", "Alice"])
assert exit_code == 0
```
