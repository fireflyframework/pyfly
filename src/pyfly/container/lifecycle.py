"""Lifecycle management for container services."""

from __future__ import annotations

import inspect
from typing import Any


async def call_lifecycle_hook(instance: Any, hook_name: str) -> None:
    """Call a lifecycle hook on an instance if it exists."""
    hook = getattr(instance, hook_name, None)
    if hook is not None and callable(hook):
        result = hook()
        if inspect.isawaitable(result):
            await result
