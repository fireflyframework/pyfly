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
"""'pyfly run' — Start a PyFly application with uvicorn."""

from __future__ import annotations

import click

from pyfly.cli.console import console


@click.command()
@click.option("--host", default="0.0.0.0", help="Bind address.")
@click.option("--port", default=8080, type=int, help="Port number.")
@click.option("--reload", "use_reload", is_flag=True, help="Enable auto-reload for development.")
@click.option("--app", "app_path", default=None, help="Application import path (e.g. 'myapp.app:Application').")
def run_command(host: str, port: int, use_reload: bool, app_path: str | None) -> None:
    """Start the PyFly application server."""
    if app_path is None:
        # Try to discover app from pyfly.yaml
        app_path = _discover_app()
        if app_path is None:
            console.print("[error]No application found.[/error]")
            console.print("[dim]Provide --app flag or create a pyfly.yaml in the current directory.[/dim]")
            raise SystemExit(1)

    console.print("[info]Starting PyFly application...[/info]")
    console.print(f"[dim]  App:    {app_path}[/dim]")
    console.print(f"[dim]  Host:   {host}:{port}[/dim]")
    console.print(f"[dim]  Reload: {'on' if use_reload else 'off'}[/dim]\n")

    try:
        import uvicorn
    except ImportError:
        console.print("[error]uvicorn is not installed.[/error]")
        console.print("[dim]Install it with: pip install 'pyfly[web]'[/dim]")
        raise SystemExit(1) from None

    uvicorn.run(app_path, host=host, port=port, reload=use_reload)


def _discover_app() -> str | None:
    """Try to discover the application from pyfly.yaml, with auto-discovery fallback.

    Resolution order:
    1. ``pyfly.app.module`` in ``pyfly.yaml`` (canonical)
    2. ``app.module`` in ``pyfly.yaml`` (flat layout)
    3. Auto-discover: look for ``src/<package>/main.py`` containing an ``app`` variable
    """
    from pathlib import Path

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
    from pathlib import Path

    src = Path("src")
    if not src.is_dir():
        return None

    for pkg_dir in sorted(src.iterdir()):
        main_py = pkg_dir / "main.py"
        if main_py.is_file():
            return f"{pkg_dir.name}.main:app"

    return None
