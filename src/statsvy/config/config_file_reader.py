"""Configuration file reading utilities."""

import tomllib
from pathlib import Path
from typing import Any

from rich.text import Text

from statsvy.utils.console import console


class ConfigFileReader:
    """Reads configuration from TOML files."""

    @staticmethod
    def read_toml(config_path: Path) -> dict[str, Any]:
        """Read configuration from a TOML file.

        Extracts the [tool.statsvy] section from pyproject.toml or
        similar TOML configuration files.

        Args:
            config_path: Path to the TOML configuration file.

        Returns:
            Dictionary containing the statsvy configuration section,
            or empty dict if file doesn't exist or section is missing.

        Raises:
            tomllib.TOMLDecodeError: If the TOML file is malformed.
        """
        if not config_path.exists():
            return {}

        with open(config_path, "rb") as f:
            try:
                data = tomllib.load(f)
            except tomllib.TOMLDecodeError as exc:
                # Provide a clear, user-friendly message but re-raise so
                # existing callers/tests that expect the exception continue to
                # receive the original error.
                console.print(
                    Text(
                        f"Failed to parse config file: {config_path} - {exc}",
                        style="red",
                    )
                )
                raise

        statsvy_config = data.get("tool", {}).get("statsvy", {})

        if not isinstance(statsvy_config, dict):
            return {}

        return statsvy_config
