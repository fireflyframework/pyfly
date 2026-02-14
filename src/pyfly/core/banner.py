"""Startup banner rendering — ASCII art, minimal, or custom file."""

from __future__ import annotations

import enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyfly.core.config import Config

_DEFAULT_BANNER = r"""
    ____        ________
   / __ \__  __/ ____/ /_  __
  / /_/ / / / / /_  / / / / /
 / ____/ /_/ / __/ / / /_/ /
/_/    \__, /_/   /_/\__, /
      /____/        /____/
""".lstrip(
    "\n"
)


class BannerMode(enum.Enum):
    TEXT = "TEXT"
    MINIMAL = "MINIMAL"
    OFF = "OFF"


class BannerPrinter:
    """Renders the PyFly startup banner."""

    def __init__(
        self,
        mode: BannerMode = BannerMode.TEXT,
        version: str = "0.1.0",
        app_name: str = "",
        app_version: str = "",
        active_profiles: list[str] | None = None,
        custom_location: str = "",
    ) -> None:
        self._mode = mode
        self._version = version
        self._app_name = app_name
        self._app_version = app_version
        self._active_profiles = active_profiles or []
        self._custom_location = custom_location

    @classmethod
    def from_config(
        cls,
        config: Config,
        version: str = "0.1.0",
        app_name: str = "",
        app_version: str = "",
        active_profiles: list[str] | None = None,
    ) -> BannerPrinter:
        """Create a BannerPrinter from application configuration."""
        mode_str = str(config.get("pyfly.banner.mode", "TEXT")).upper()
        try:
            mode = BannerMode(mode_str)
        except ValueError:
            mode = BannerMode.TEXT
        location = config.get("pyfly.banner.location", "") or ""
        return cls(
            mode=mode,
            version=version,
            app_name=app_name,
            app_version=app_version,
            active_profiles=active_profiles,
            custom_location=str(location),
        )

    def render(self) -> str:
        """Render the banner as a string."""
        if self._mode == BannerMode.OFF:
            return ""

        if self._mode == BannerMode.MINIMAL:
            return f":: PyFly :: (v{self._version})"

        # TEXT mode — custom file or default
        banner_text = self._load_custom_banner()
        if banner_text is None:
            banner_text = _DEFAULT_BANNER

        banner_text = self._replace_placeholders(banner_text)
        framework_line = f":: PyFly Framework :: (v{self._version})"
        return banner_text.rstrip("\n") + "\n\n" + framework_line

    def _load_custom_banner(self) -> str | None:
        """Load custom banner file, returning None if not found or unreadable."""
        if not self._custom_location:
            return None
        path = Path(self._custom_location)
        if not path.exists():
            return None
        try:
            return path.read_text()
        except (OSError, UnicodeDecodeError):
            return None

    def _replace_placeholders(self, text: str) -> str:
        """Replace ${...} placeholders in banner text."""
        profiles_str = ", ".join(self._active_profiles) if self._active_profiles else ""
        replacements = {
            "${pyfly.version}": self._version,
            "${app.name}": self._app_name,
            "${app.version}": self._app_version,
            "${profiles.active}": profiles_str,
        }
        for placeholder, value in replacements.items():
            text = text.replace(placeholder, value)
        return text
