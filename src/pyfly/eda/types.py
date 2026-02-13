"""EDA types and data structures."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class EventEnvelope:
    """Envelope wrapping an event with metadata."""

    event_type: str
    payload: dict[str, Any]
    destination: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    headers: dict[str, str] = field(default_factory=dict)
