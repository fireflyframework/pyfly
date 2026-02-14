"""Messaging data types."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Message:
    topic: str
    value: bytes
    key: bytes | None = None
    headers: dict[str, str] = field(default_factory=dict)
