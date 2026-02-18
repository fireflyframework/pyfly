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
"""'pyfly run' — Start a PyFly application with swappable server adapters."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from pyfly.cli.console import console


def _ensure_src_on_path() -> None:
    """Add ``src/`` to sys.path when running from a src-layout project.

    This allows ``pyfly run`` to work without ``pip install -e .`` first,
    mirroring how ``uvicorn --app-dir src`` works.
    """
    src = Path("src").resolve()
    if src.is_dir():
        src_str = str(src)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)


@click.command()
@click.option("--host", default="0.0.0.0", help="Bind address.")
@click.option("--port", default=None, type=int, help="Port number (default: from pyfly.yaml or 8080).")
@click.option("--reload", "use_reload", is_flag=True, help="Enable auto-reload for development.")
@click.option("--app", "app_path", default=None, help="Application import path (e.g. 'myapp.main:app').")
@click.option("--server", "server_type", default=None, help="Server type: granian|uvicorn|hypercorn.")
@click.option("--workers", "workers", default=None, type=int, help="Number of worker processes.")
def run_command(
    host: str,
    port: int | None,
    use_reload: bool,
    app_path: str | None,
    server_type: str | None,
    workers: int | None,
) -> None:
    """Start the PyFly application server."""
    _ensure_src_on_path()

    if app_path is None:
        app_path = _discover_app()
        if app_path is None:
            console.print("[error]No application found.[/error]")
            console.print("[dim]Provide --app flag or create a pyfly.yaml in the current directory.[/dim]")
            raise SystemExit(1)

    if port is None:
        port = _read_port_from_config() or 8080

    # --reload falls back to uvicorn (only server with a built-in file watcher)
    if use_reload:
        _run_with_uvicorn_reload(app_path, host, port)
        return

    # Resolve server and event loop
    server_adapter, event_loop_adapter, config = _resolve_server_adapter(
        server_type, host, port, workers,
    )

    if event_loop_adapter is not None:
        event_loop_adapter.install()

    # Attach host/port to config
    config.host = host
    config.port = port

    server_adapter.serve(app_path, config)


# ---------------------------------------------------------------------------
# Helper functions for server resolution
# ---------------------------------------------------------------------------


def _resolve_server_adapter(
    server_type: str | None,
    host: str,
    port: int,
    workers: int | None,
) -> tuple:
    """Build a (server_adapter, event_loop_adapter, config) triple."""
    from pyfly.config.properties.server import ServerProperties  # noqa: F811

    config = _load_server_properties()
    if server_type:
        config.type = server_type
    if workers is not None:
        config.workers = workers
    server_adapter = _create_server_adapter(config.type)
    event_loop_adapter = _create_event_loop_adapter(config.event_loop)
    return server_adapter, event_loop_adapter, config


def _create_server_adapter(server_type: str):  # noqa: ANN201
    """Create server adapter by type or auto-detect best available."""
    if server_type in ("granian", "auto"):
        try:
            from pyfly.server.adapters.granian.adapter import GranianServerAdapter

            return GranianServerAdapter()
        except ImportError:
            if server_type == "granian":
                console.print("[error]granian is not installed.[/error]")
                raise SystemExit(1) from None

    if server_type in ("uvicorn", "auto"):
        try:
            from pyfly.server.adapters.uvicorn.adapter import UvicornServerAdapter

            return UvicornServerAdapter()
        except ImportError:
            if server_type == "uvicorn":
                console.print("[error]uvicorn is not installed.[/error]")
                raise SystemExit(1) from None

    if server_type in ("hypercorn", "auto"):
        try:
            from pyfly.server.adapters.hypercorn.adapter import HypercornServerAdapter

            return HypercornServerAdapter()
        except ImportError:
            if server_type == "hypercorn":
                console.print("[error]hypercorn is not installed.[/error]")
                raise SystemExit(1) from None

    console.print("[error]No ASGI server available.[/error]")
    raise SystemExit(1)


def _create_event_loop_adapter(event_loop: str):  # noqa: ANN201
    """Create event loop adapter by name or auto-detect."""
    if event_loop in ("uvloop", "auto"):
        try:
            from pyfly.server.adapters.event_loop.uvloop_adapter import UvloopEventLoopAdapter

            return UvloopEventLoopAdapter()
        except ImportError:
            if event_loop == "uvloop":
                return None

    if event_loop in ("winloop", "auto"):
        try:
            from pyfly.server.adapters.event_loop.winloop_adapter import WinloopEventLoopAdapter

            return WinloopEventLoopAdapter()
        except ImportError:
            if event_loop == "winloop":
                return None

    from pyfly.server.adapters.event_loop.asyncio_adapter import AsyncioEventLoopAdapter

    return AsyncioEventLoopAdapter()


def _load_server_properties():  # noqa: ANN201
    """Load ServerProperties from pyfly.yaml, falling back to defaults."""
    from pyfly.config.properties.server import ServerProperties

    try:
        import yaml

        config_path = Path("pyfly.yaml")
        if config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}
            server_data = (data.get("pyfly", {}) or {}).get("server", {}) or {}
            return ServerProperties(**{
                k.replace("-", "_"): v
                for k, v in server_data.items()
                if k.replace("-", "_") in ServerProperties.__dataclass_fields__
                and not isinstance(v, dict)
            })
    except Exception:
        pass
    return ServerProperties()


def _run_with_uvicorn_reload(app_path: str, host: str, port: int) -> None:
    """Run with uvicorn in reload mode (development only)."""
    try:
        import uvicorn
    except ImportError:
        console.print("[error]uvicorn is required for --reload mode.[/error]")
        raise SystemExit(1) from None
    uvicorn.run(app_path, host=host, port=port, reload=True, log_level="warning")


# ---------------------------------------------------------------------------
# Existing helper functions (unchanged)
# ---------------------------------------------------------------------------


def _read_port_from_config() -> int | None:
    """Read the web port from pyfly.yaml if available."""
    import yaml  # type: ignore[import-untyped]

    config_path = Path("pyfly.yaml")
    if not config_path.exists():
        return None
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
        pyfly_section = config.get("pyfly", {}) or {}
        web_section = pyfly_section.get("web", {}) or {}
        port = web_section.get("port")
        return int(port) if port is not None else None
    except Exception:
        return None


def _discover_app() -> str | None:
    """Try to discover the application from pyfly.yaml, with auto-discovery fallback.

    Resolution order:
    1. ``pyfly.app.module`` in ``pyfly.yaml`` (canonical)
    2. ``app.module`` in ``pyfly.yaml`` (flat layout)
    3. Auto-discover: look for ``src/<package>/main.py`` containing an ``app`` variable
    """
    import yaml

    config_path = Path("pyfly.yaml")
    if not config_path.exists():
        return None

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        if not config:
            return _auto_discover_module()
        # Support both pyfly.app.module (canonical) and flat app.module
        pyfly_section = config.get("pyfly", {}) or {}
        app_section = pyfly_section.get("app", config.get("app", {})) or {}
        if "module" in app_section:
            return str(app_section["module"])
    except Exception:
        pass

    return _auto_discover_module()


def _auto_discover_module() -> str | None:
    """Scan src/ for a main.py that likely contains the ASGI app."""
    src = Path("src")
    if not src.is_dir():
        return None

    for pkg_dir in sorted(src.iterdir()):
        main_py = pkg_dir / "main.py"
        if main_py.is_file():
            return f"{pkg_dir.name}.main:app"

    return None
