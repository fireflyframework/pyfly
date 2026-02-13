"""Container types and enums."""

from enum import Enum, auto


class Scope(Enum):
    """Bean lifecycle scope."""

    SINGLETON = auto()
    TRANSIENT = auto()
    REQUEST = auto()
