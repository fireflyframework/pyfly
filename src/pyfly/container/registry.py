"""Service registration metadata."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pyfly.container.types import Scope


@dataclass
class Registration:
    """Metadata for a registered service."""

    impl_type: type
    scope: Scope = Scope.SINGLETON
    condition: Callable[..., bool] | None = None
    instance: Any = field(default=None, repr=False)
