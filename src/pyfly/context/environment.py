"""Environment — unified property access with profile support."""

from __future__ import annotations

import os
from typing import Any

from pyfly.core.config import Config


class Environment:
    """Provides access to configuration properties and active profiles.

    Profiles are loaded from (in priority order):
    1. ``PYFLY_PROFILES_ACTIVE`` environment variable
    2. ``pyfly.profiles.active`` config property
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._active_profiles = self._load_profiles()

    @property
    def active_profiles(self) -> list[str]:
        """Currently active profiles."""
        return list(self._active_profiles)

    def accepts_profiles(self, *profiles: str) -> bool:
        """Return True if any of the given profiles are active."""
        return any(p in self._active_profiles for p in profiles)

    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a configuration property by dotted key."""
        return self._config.get(key, default)

    def _load_profiles(self) -> list[str]:
        """Load active profiles from env var or config."""
        env_profiles = os.environ.get("PYFLY_PROFILES_ACTIVE", "")
        if env_profiles:
            return [p.strip() for p in env_profiles.split(",") if p.strip()]

        config_profiles = self._config.get("pyfly.profiles.active", "")
        if config_profiles:
            return [p.strip() for p in str(config_profiles).split(",") if p.strip()]

        return []
