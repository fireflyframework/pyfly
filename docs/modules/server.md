# Server Module Guide

The PyFly server module provides a pluggable ASGI server and event loop abstraction layer. It follows the same hexagonal (ports-and-adapters) pattern as the web module: framework-agnostic port interfaces (`ApplicationServerPort`, `EventLoopPort`) define the contracts, while swappable adapters (Granian, Uvicorn, Hypercorn) provide the concrete implementations. A cascading auto-configuration mechanism selects the best available server and event loop at startup based on installed libraries.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Server Selection](#server-selection)
  - [Granian (Default)](#granian-default)
  - [Uvicorn](#uvicorn)
  - [Hypercorn](#hypercorn)
- [Event Loop Selection](#event-loop-selection)
  - [uvloop (Linux/macOS)](#uvloop-linuxmacos)
  - [winloop (Windows)](#winloop-windows)
  - [asyncio (Fallback)](#asyncio-fallback)
- [Auto-Configuration](#auto-configuration)
  - [Cascading @conditional_on_class](#cascading-conditional_on_class)
  - [ServerAutoConfiguration](#serverautoconfiguration)
  - [EventLoopAutoConfiguration](#eventloopautoconfiguration)
- [Configuration Reference](#configuration-reference)
  - [ServerProperties](#serverproperties)
  - [Full YAML Reference](#full-yaml-reference)
- [CLI: pyfly run](#cli-pyfly-run)
- [Custom Server Adapter](#custom-server-adapter)
- [Spring Boot Comparison](#spring-boot-comparison)
- [Source Files](#source-files)

---

## Architecture Overview

PyFly's server module is organized into three tiers, mirroring the web module's structure:

1. **Framework-agnostic core** (`pyfly.server`): The `ServerProperties` dataclass for configuration binding, and the port protocols that define what a server and event loop must do. These contain no server-specific code.

2. **Port interfaces** (`pyfly.server.ports`): The `ApplicationServerPort` protocol defines the contract for running an ASGI application, and the `EventLoopPort` protocol defines the contract for configuring the asyncio event loop policy. These ensure that the application layer never depends directly on Granian, Uvicorn, or any other server.

3. **Server adapters** (`pyfly.server.adapters`): Concrete implementations that translate the port contracts into server-specific calls. Granian, Uvicorn, and Hypercorn adapters each implement `ApplicationServerPort`. uvloop, winloop, and asyncio adapters each implement `EventLoopPort`.

```
pyfly.server/
    __init__.py              # Public API exports
    ports/
        __init__.py
        outbound.py          # ApplicationServerPort, EventLoopPort protocols
    adapters/
        granian.py           # GranianServerAdapter (ApplicationServerPort impl)
        uvicorn.py           # UvicornServerAdapter (ApplicationServerPort impl)
        hypercorn.py         # HypercornServerAdapter (ApplicationServerPort impl)
        uvloop.py            # UvloopEventLoopAdapter (EventLoopPort impl)
        winloop.py           # WinloopEventLoopAdapter (EventLoopPort impl)
        asyncio.py           # AsyncioEventLoopAdapter (EventLoopPort impl)
    auto_configuration.py    # ServerAutoConfiguration, EventLoopAutoConfiguration
    properties.py            # ServerProperties dataclass
```

The relationship between the web and server modules:

- **`WebServerPort`** creates the ASGI application (Starlette or FastAPI).
- **`ApplicationServerPort`** runs that ASGI application on a network socket.
- **`EventLoopPort`** configures the event loop policy before the server starts.

```
EventLoopPort          ApplicationServerPort          WebServerPort
  (uvloop)      --->     (Granian/Uvicorn)      --->   (Starlette/FastAPI)
  configures             serves                        creates
  event loop             ASGI app                      ASGI app
```

---

## Server Selection

PyFly supports three ASGI servers. When `pyfly.server.type` is set to `"auto"` (the default), the framework selects the highest-priority server that is installed.

### Granian (Default)

**Priority:** Highest (selected first when installed)

Granian is a Rust-powered ASGI server built on tokio. It provides the highest throughput of any Python ASGI server, with native HTTP/2 support and efficient worker management.

- ~112K requests/second (single worker, plain text)
- Native HTTP/2 without TLS termination
- Rust/tokio thread pool for I/O
- Per-worker runtime thread configuration

Install: `pip install 'pyfly[granian]'` or `pip install 'pyfly[web-fast]'`

See [Granian Adapter Guide](../adapters/granian.md) for details.

### Uvicorn

**Priority:** Medium (selected when Granian is not installed)

Uvicorn is the ecosystem-standard ASGI server. It is widely used, well-documented, and compatible with virtually all ASGI frameworks.

- ~37K requests/second (single worker, plain text)
- Mature ecosystem with extensive documentation
- `--reload` support for development
- Built-in HTTP/1.1 (HTTP/2 via httptools)

Install: `pip install 'pyfly[web]'` (included by default with the web extra)

### Hypercorn

**Priority:** Lowest (selected when neither Granian nor Uvicorn is installed)

Hypercorn is an ASGI server with native HTTP/2 and HTTP/3 (QUIC) support. It is the only Python ASGI server that supports HTTP/3 without an external reverse proxy.

- HTTP/2 and HTTP/3 (QUIC) support
- WebSocket over HTTP/2
- Trio and asyncio event loop support

Install: `pip install 'pyfly[hypercorn]'`

### Selection Priority

| Priority | Server | Condition |
|----------|--------|-----------|
| 1 | Granian | `granian` is importable |
| 2 | Uvicorn | `uvicorn` is importable |
| 3 | Hypercorn | `hypercorn` is importable |

If none are installed, the application exits with an error suggesting the `web` extra.

---

## Event Loop Selection

PyFly supports pluggable event loop implementations. When `pyfly.server.event-loop` is set to `"auto"` (the default), the framework selects the best available loop for the current platform.

### uvloop (Linux/macOS)

**Priority:** Highest on Linux and macOS

uvloop is a fast, drop-in replacement for asyncio's default event loop, built on libuv (the same library that powers Node.js). It provides 2-4x throughput improvement over the default asyncio loop.

Install: `pip install 'pyfly[web-fast]'` or `pip install uvloop`

### winloop (Windows)

**Priority:** Highest on Windows

winloop is the Windows equivalent of uvloop, providing the same libuv-based performance on Windows platforms.

Install: `pip install winloop`

### asyncio (Fallback)

**Priority:** Always available

The standard library asyncio event loop is always available and requires no additional dependencies. It is used as the fallback when neither uvloop nor winloop is installed.

### Selection Priority

| Priority | Event Loop | Platform | Condition |
|----------|-----------|----------|-----------|
| 1 | uvloop | Linux/macOS | `uvloop` is importable |
| 1 | winloop | Windows | `winloop` is importable |
| 2 | asyncio | All | Always available |

---

## Auto-Configuration

Server and event loop selection uses the same decentralized auto-configuration pattern as the rest of PyFly. Each adapter is guarded by `@conditional_on_class` and `@conditional_on_missing_bean` decorators, forming a cascading priority chain.

### Cascading @conditional_on_class

The cascading pattern works by registering multiple auto-configuration classes for the same port, each guarded by different conditions. The first one whose conditions are satisfied wins, because subsequent configurations are guarded by `@conditional_on_missing_bean`.

For servers, the cascade is:

1. **GranianAutoConfiguration** -- `@conditional_on_class("granian")` + `@conditional_on_missing_bean(ApplicationServerPort)`. If Granian is installed and no server bean exists, register `GranianServerAdapter`.
2. **UvicornAutoConfiguration** -- `@conditional_on_class("uvicorn")` + `@conditional_on_missing_bean(ApplicationServerPort)`. If Uvicorn is installed and no server bean exists (because Granian was not installed), register `UvicornServerAdapter`.
3. **HypercornAutoConfiguration** -- `@conditional_on_class("hypercorn")` + `@conditional_on_missing_bean(ApplicationServerPort)`. Fallback if neither Granian nor Uvicorn is installed.

Because auto-configuration classes are processed in entry-point order, and each checks `@conditional_on_missing_bean`, the first matching configuration wins. This is the same pattern Spring Boot uses for embedded server selection (Tomcat > Jetty > Undertow).

### ServerAutoConfiguration

```python
@auto_configuration
@conditional_on_class("granian")
@conditional_on_missing_bean(ApplicationServerPort)
class GranianServerAutoConfiguration:
    """Auto-configures Granian when available."""

    @bean
    def application_server(self, config: Config) -> ApplicationServerPort:
        from pyfly.server.adapters.granian import GranianServerAdapter
        return GranianServerAdapter(config)
```

Each server auto-configuration class follows this pattern. The three classes are registered as separate entry points:

```toml
[project.entry-points."pyfly.auto_configuration"]
server_granian  = "pyfly.server.auto_configuration:GranianServerAutoConfiguration"
server_uvicorn  = "pyfly.server.auto_configuration:UvicornServerAutoConfiguration"
server_hypercorn = "pyfly.server.auto_configuration:HypercornServerAutoConfiguration"
```

### EventLoopAutoConfiguration

Event loop auto-configuration follows the same cascading pattern:

```python
@auto_configuration
@conditional_on_class("uvloop")
@conditional_on_missing_bean(EventLoopPort)
class UvloopAutoConfiguration:
    """Auto-configures uvloop when available."""

    @bean
    def event_loop(self) -> EventLoopPort:
        from pyfly.server.adapters.uvloop import UvloopEventLoopAdapter
        return UvloopEventLoopAdapter()
```

The event loop adapter's `configure()` method is called before the server starts, setting the asyncio event loop policy:

```python
class UvloopEventLoopAdapter:
    def configure(self) -> None:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
```

---

## Configuration Reference

### ServerProperties

The `ServerProperties` dataclass (`src/pyfly/server/properties.py`) captures all server configuration under the `pyfly.server.*` namespace:

```python
from pyfly.core.config import config_properties
from dataclasses import dataclass, field


@config_properties(prefix="pyfly.server")
@dataclass
class ServerProperties:
    type: str = "auto"
    event_loop: str = "auto"
    workers: int = 0
    backlog: int = 1024
    graceful_timeout: int = 30
    http: str = "auto"
    keep_alive_timeout: int = 5
    granian: dict = field(default_factory=lambda: {
        "runtime_threads": 1,
        "runtime_mode": "auto",
    })
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `type` | `str` | `"auto"` | Server selection: `auto`, `granian`, `uvicorn`, `hypercorn` |
| `event_loop` | `str` | `"auto"` | Event loop selection: `auto`, `uvloop`, `winloop`, `asyncio` |
| `workers` | `int` | `0` | Worker count (`0` = `os.cpu_count()`) |
| `backlog` | `int` | `1024` | TCP listen backlog |
| `graceful_timeout` | `int` | `30` | Seconds to wait for in-flight requests during shutdown |
| `http` | `str` | `"auto"` | HTTP version: `auto`, `1`, `2` |
| `keep_alive_timeout` | `int` | `5` | Keep-alive timeout in seconds |
| `granian.runtime_threads` | `int` | `1` | Granian runtime threads per worker |
| `granian.runtime_mode` | `str` | `"auto"` | Granian runtime mode (`auto`, `st`, `mt`) |

### Full YAML Reference

```yaml
pyfly:
  server:
    type: "auto"              # auto | granian | uvicorn | hypercorn
    event-loop: "auto"        # auto | uvloop | winloop | asyncio
    workers: 0                # 0 = cpu_count
    backlog: 1024             # TCP listen backlog
    graceful-timeout: 30      # Seconds to wait for in-flight requests
    http: "auto"              # auto | 1 | 2
    keep-alive-timeout: 5     # Keep-alive timeout in seconds
    granian:
      runtime-threads: 1      # Granian runtime threads per worker
      runtime-mode: "auto"    # auto | st (single-thread) | mt (multi-thread)
```

**Workers:** When `workers: 0` (the default), the framework uses `os.cpu_count()` to determine the number of workers. Set to `1` for development or single-core containers.

**HTTP version:** When `http: "auto"`, the server selects the best HTTP version it supports. Granian defaults to HTTP/2; Uvicorn defaults to HTTP/1.1; Hypercorn supports HTTP/1.1, HTTP/2, and HTTP/3.

---

## CLI: pyfly run

The `pyfly run` command accepts server-related flags that override the YAML configuration:

```bash
pyfly run [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--server` | From config or `auto` | Server type: `granian`, `uvicorn`, `hypercorn` |
| `--workers` | From config or `0` | Number of worker processes |
| `--host` | `0.0.0.0` | Bind address |
| `--port` | From `pyfly.yaml` or `8080` | Port number |
| `--reload` | `false` | Enable auto-reload on code changes |
| `--app` | Auto-discovered | Application import path |

### Examples

```bash
# Auto-select server (highest-priority installed)
pyfly run

# Force Granian with 4 workers
pyfly run --server granian --workers 4

# Development with Uvicorn and auto-reload
pyfly run --server uvicorn --reload

# Production with Granian on all cores
pyfly run --server granian --workers 0
```

**Flag precedence:** CLI flags override YAML configuration. The resolution order is: CLI flag > `pyfly.server.*` in config > default value.

---

## Custom Server Adapter

To implement a custom ASGI server adapter, implement the `ApplicationServerPort` protocol and register it as a bean. The `@conditional_on_missing_bean` guard on the built-in auto-configurations ensures your bean takes precedence.

### ApplicationServerPort Protocol

```python
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ApplicationServerPort(Protocol):
    def run(self, app: Any, host: str, port: int, **kwargs: Any) -> None:
        """Start the ASGI server with the given application."""
        ...
```

### EventLoopPort Protocol

```python
@runtime_checkable
class EventLoopPort(Protocol):
    def configure(self) -> None:
        """Set the asyncio event loop policy."""
        ...
```

### Example: Custom Server Adapter

```python
from pyfly.container import configuration
from pyfly.container.bean import bean
from pyfly.server.ports.outbound import ApplicationServerPort


@configuration
class CustomServerConfig:
    @bean
    def application_server(self) -> ApplicationServerPort:
        return MyCustomServerAdapter()


class MyCustomServerAdapter:
    def run(self, app, host: str, port: int, **kwargs) -> None:
        import my_server
        my_server.run(app, host=host, port=port, **kwargs)
```

Because the user-provided `@bean` is processed before auto-configurations, the `@conditional_on_missing_bean(ApplicationServerPort)` guard on all built-in server auto-configurations will evaluate to `False`, and the built-in adapters will be skipped.

---

## Spring Boot Comparison

PyFly's server abstraction mirrors Spring Boot's embedded server architecture:

| Spring Boot | PyFly | Purpose |
|-------------|-------|---------|
| `WebServer` interface | `ApplicationServerPort` protocol | Contract for running the HTTP server |
| `EventLoopGroup` (Netty) | `EventLoopPort` protocol | Contract for the event loop / I/O runtime |
| `server.port` | `pyfly.server.port` via `pyfly.web.port` | HTTP listen port |
| `server.tomcat.*` | `pyfly.server.granian.*` | Server-specific tuning properties |
| `server.servlet.context-path` | `pyfly.web.base-path` | Application base path |
| Tomcat (default) | Granian (default) | Highest-priority embedded server |
| Jetty (fallback) | Uvicorn (fallback) | Ecosystem-standard fallback |
| Undertow (alternative) | Hypercorn (alternative) | Advanced protocol support |
| `TomcatServletWebServerFactory` | `GranianServerAutoConfiguration` | Server-specific auto-configuration |

**Key similarities:**

- Both use conditional bean registration to cascade through server implementations (Tomcat > Jetty > Undertow in Spring; Granian > Uvicorn > Hypercorn in PyFly).
- Both allow users to override the auto-configured server by providing their own bean.
- Both support server-specific tuning via namespaced configuration properties.
- Both configure the I/O runtime (Netty's `EventLoopGroup` / asyncio's event loop policy) separately from the server itself.

---

## Source Files

- `src/pyfly/server/__init__.py` -- top-level re-exports
- `src/pyfly/server/ports/outbound.py` -- `ApplicationServerPort`, `EventLoopPort`
- `src/pyfly/server/properties.py` -- `ServerProperties`
- `src/pyfly/server/auto_configuration.py` -- `GranianServerAutoConfiguration`, `UvicornServerAutoConfiguration`, `HypercornServerAutoConfiguration`, `UvloopAutoConfiguration`
- `src/pyfly/server/adapters/granian.py` -- `GranianServerAdapter`
- `src/pyfly/server/adapters/uvicorn.py` -- `UvicornServerAdapter`
- `src/pyfly/server/adapters/hypercorn.py` -- `HypercornServerAdapter`
- `src/pyfly/server/adapters/uvloop.py` -- `UvloopEventLoopAdapter`
- `src/pyfly/server/adapters/winloop.py` -- `WinloopEventLoopAdapter`
- `src/pyfly/server/adapters/asyncio.py` -- `AsyncioEventLoopAdapter`

---

## Adapters

- [Granian Adapter](../adapters/granian.md) -- Setup, configuration reference, and benchmarks for the Granian ASGI server
- [Starlette Adapter](../adapters/starlette.md) -- Setup, configuration, and adapter-specific features for the Starlette web adapter
- [FastAPI Adapter](../adapters/fastapi.md) -- Setup, configuration, and adapter-specific features for the FastAPI web adapter
