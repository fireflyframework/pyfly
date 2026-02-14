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
"""Type-safe configuration with YAML/TOML files, env vars, and dataclass binding."""

from __future__ import annotations

import dataclasses
import importlib.resources
import os
import tomllib
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
    def from_file(
        cls,
        path: str | Path,
        active_profiles: list[str] | None = None,
        load_defaults: bool = True,
    ) -> Config:
        """Load configuration from a YAML or TOML file, merging profile-specific overlays.

        Merge order (later wins):
        1. Framework defaults (pyfly-defaults.yaml from pyfly.resources)
        2. Base config (pyfly.yaml or pyfly.toml)
        3. pyfly-{profile}.yaml/toml for each active profile, in order
        4. Environment variables (handled at read time in get())
        """
        # 1. Load framework defaults as base layer
        data: dict[str, Any] = {}
        if load_defaults:
            data = cls._load_framework_defaults()

        # 2. Load user config file
        path = Path(path)
        if path.exists():
            user_data = cls._load_config_data(path)
            data = cls._deep_merge(data, user_data)

        # 3. Merge profile overlays
        if path.exists():
            for profile in active_profiles or []:
                profile_path = path.parent / f"{path.stem}-{profile}{path.suffix}"
                if profile_path.exists():
                    profile_data = cls._load_config_data(profile_path)
                    data = cls._deep_merge(data, profile_data)

        return cls(data)

    @staticmethod
    def _load_config_data(path: Path) -> dict[str, Any]:
        """Load config data from a YAML or TOML file."""
        if path.suffix == ".toml":
            with open(path, "rb") as f:
                return tomllib.load(f) or {}
        with open(path) as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def _load_framework_defaults() -> dict[str, Any]:
        """Load built-in framework defaults from pyfly.resources."""
        defaults_file = importlib.resources.files("pyfly.resources").joinpath(
            "pyfly-defaults.yaml"
        )
        with importlib.resources.as_file(defaults_file) as p:
            with open(p) as f:
                return yaml.safe_load(f) or {}

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
        # Check environment variable override: pyfly.app.name -> PYFLY_APP_NAME
        env_base = key.removeprefix("pyfly.") if key.startswith("pyfly.") else key
        env_key = "PYFLY_" + env_base.upper().replace(".", "_").replace("-", "_")
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
