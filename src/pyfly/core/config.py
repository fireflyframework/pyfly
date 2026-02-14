"""Type-safe configuration with YAML files, env vars, and dataclass binding."""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import Any, TypeVar, get_type_hints

import yaml

T = TypeVar("T")

_CONFIG_PROPERTIES_ATTR = "__pyfly_config_prefix__"


def config_properties(prefix: str):
    """Mark a dataclass as bindable to a configuration prefix.

    Usage:
        @config_properties(prefix="database")
        @dataclass
        class DatabaseConfig:
            url: str = "sqlite:///test.db"
    """

    def decorator(cls: type[T]) -> type[T]:
        setattr(cls, _CONFIG_PROPERTIES_ATTR, prefix)
        return cls

    return decorator


class Config:
    """Hierarchical configuration with dot-notation access and env var overrides.

    Priority (highest wins):
    1. Environment variables (PYFLY_SECTION_KEY format)
    2. Configuration dict / YAML file values
    3. Dataclass defaults
    """

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data: dict[str, Any] = data or {}

    @classmethod
    def from_file(cls, path: str | Path, active_profiles: list[str] | None = None) -> Config:
        """Load configuration from a YAML file, merging profile-specific overlays.

        Merge order (later wins):
        1. Base config (pyfly.yaml)
        2. pyfly-{profile}.yaml for each active profile, in order
        3. Environment variables (handled at read time in get())
        """
        path = Path(path)
        if not path.exists():
            return cls({})
        with open(path) as f:
            data = yaml.safe_load(f) or {}

        for profile in active_profiles or []:
            profile_path = path.parent / f"{path.stem}-{profile}{path.suffix}"
            if profile_path.exists():
                with open(profile_path) as f:
                    profile_data = yaml.safe_load(f) or {}
                data = cls._deep_merge(data, profile_data)

        return cls(data)

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Recursively merge override into base, with override values winning."""
        merged = dict(base)
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = Config._deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by dot-notation key, checking env vars first.

        Args:
            key: Dot-separated key path (e.g. "app.name").
            default: Value to return if key is not found.
        """
        # Check environment variable override: app.name -> PYFLY_APP_NAME
        env_key = "PYFLY_" + key.upper().replace(".", "_")
        env_val = os.environ.get(env_key)
        if env_val is not None:
            return env_val

        # Walk nested dict
        parts = key.split(".")
        current: Any = self._data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return default
            else:
                return default
        return current

    def get_section(self, prefix: str) -> dict[str, Any]:
        """Get all values under a prefix as a flat dict."""
        parts = prefix.split(".")
        current: Any = self._data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part, {})
            else:
                return {}
        return current if isinstance(current, dict) else {}

    def bind(self, config_cls: type[T]) -> T:
        """Bind configuration to a @config_properties dataclass."""
        prefix = getattr(config_cls, _CONFIG_PROPERTIES_ATTR, None)
        if prefix is None:
            raise ValueError(f"{config_cls.__name__} is not decorated with @config_properties")

        section = self.get_section(prefix)
        hints = get_type_hints(config_cls)

        # Build kwargs from config, falling back to dataclass defaults
        kwargs: dict[str, Any] = {}
        for field in dataclasses.fields(config_cls):
            if field.name in section:
                value = section[field.name]
                # Coerce type if needed
                expected_type = hints.get(field.name)
                if expected_type is int and isinstance(value, str):
                    value = int(value)
                elif expected_type is float and isinstance(value, str):
                    value = float(value)
                elif expected_type is bool and isinstance(value, str):
                    value = value.lower() in ("true", "1", "yes")
                kwargs[field.name] = value

        return config_cls(**kwargs)
