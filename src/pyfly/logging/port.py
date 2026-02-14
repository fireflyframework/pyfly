"""LoggingPort — the hexagonal port for framework logging."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pyfly.core.config import Config


@runtime_checkable
class LoggingPort(Protocol):
    """Port defining the logging contract for PyFly."""

    def configure(self, config: Config) -> None: ...
    def get_logger(self, name: str) -> Any: ...
    def set_level(self, name: str, level: str) -> None: ...
