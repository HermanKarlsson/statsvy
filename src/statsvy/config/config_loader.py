"""Configuration loading and merge coordination."""

from dataclasses import replace
from pathlib import Path

from rich.text import Text

from statsvy.config.config_env_reader import ConfigEnvReader
from statsvy.config.config_file_reader import ConfigFileReader
from statsvy.config.config_value_converter import (
    ConfigInput,
    ConfigValueConverter,
)
from statsvy.data.config import Config
from statsvy.utils.console import console


class ConfigLoader:
    """Coordinates loading and merging configurations from multiple sources.

    This class manages the configuration lifecycle for Statsvy, ensuring a
    specific order of precedence:
    1. Default values in the Config instance.
    2. Settings from a config file (e.g., pyproject.toml).
    3. Environment variables (prefixed with STATSVY_).
    4. Explicit overrides from the Command Line Interface (CLI).

    Attributes:
        config_path: The file path to the TOML configuration file.
        config: The immutable Config instance containing current settings.
    """

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the ConfigLoader.

        Args:
            config_path: Optional path to the configuration file.
                Defaults to pyproject.toml in current working directory.
        """
        if config_path is None:
            # Prefer pyproject.toml if present; otherwise fall back to statsvy.toml.
            cwd = Path.cwd()
            pyproject = cwd / "pyproject.toml"
            statsvy_toml = cwd / "statsvy.toml"
            if pyproject.exists():
                config_path = pyproject
            elif statsvy_toml.exists():
                config_path = statsvy_toml
            else:
                # keep existing default behaviour when neither file exists
                config_path = pyproject
        self.config_path = config_path
        self.config: Config = Config.default()

    def load(self) -> None:
        """Load configuration from the TOML file and environment variables.

        This method reads the [tool.statsvy] section of the TOML file
        if it exists, updates the internal config, and then applies
        environment variable overrides.
        """
        # Load from file
        file_config = ConfigFileReader.read_toml(self.config_path)
        self._update_config_from_dict(file_config, source="file")

        # Apply environment overrides
        self._load_from_env()

    def update_from_cli(self, **kwargs: ConfigInput) -> None:
        """Update configuration settings from CLI arguments.

        Expects arguments in the format 'section_setting'. For example,
        'core_verbose' would update the 'verbose' key in the 'core' section.

        Args:
            **kwargs: Dynamic keyword arguments where keys represent config
                paths and values represent the new setting.
        """
        for key, value in kwargs.items():
            if self._should_skip_update(key, value):
                continue

            section, setting = self._parse_config_key(key)
            if section and setting:
                self._update_section_setting(section, setting, value, source="cli")

    @staticmethod
    def _should_skip_update(key: str, value: ConfigInput) -> bool:
        """Check if a config update should be skipped.

        Args:
            key: Configuration key.
            value: Configuration value.

        Returns:
            True if update should be skipped, False otherwise.
        """
        return value is None or "_" not in key

    @staticmethod
    def _parse_config_key(key: str) -> tuple[str | None, str | None]:
        """Parse a config key into section and setting parts.

        Args:
            key: Configuration key in format 'section_setting'.

        Returns:
            Tuple of (section, setting) or (None, None) if invalid.
        """
        parts = key.split("_", 1)
        if len(parts) != 2:
            return None, None
        return parts[0], parts[1]

    def _load_from_env(self) -> None:
        """Apply configuration overrides from environment variables."""
        env_overrides = ConfigEnvReader.read_env_overrides(self.config)

        for section, settings in env_overrides.items():
            for key, value in settings.items():
                self._update_section_setting(section, key, value, source="env")

    def _update_config_from_dict(
        self,
        config_dict: dict[str, dict[str, str] | list[str] | bool | int | str],
        source: str,
    ) -> None:
        """Update the Config object from a dictionary.

        Args:
            config_dict: Dictionary structure parsed from TOML.
            source: Source identifier for logging (e.g., 'file', 'env').
        """
        for section, values in config_dict.items():
            if not hasattr(self.config, section):
                continue

            if not isinstance(values, dict):
                continue

            for key, value in values.items():
                self._update_section_setting(section, key, value, source=source)

    def _update_section_setting(
        self,
        section: str,
        setting: str,
        value: ConfigInput,
        source: str,
    ) -> None:
        """Update a specific section setting if it exists.

        Args:
            section: Configuration section name.
            setting: Setting name within the section.
            value: New value for the setting.
            source: Source identifier for logging.
        """
        section_obj = getattr(self.config, section, None)
        if section_obj is None or not hasattr(section_obj, setting):
            return

        current_value = getattr(section_obj, setting)
        try:
            normalized = ConfigValueConverter.normalize_value(value, current_value)
        except (TypeError, ValueError) as exc:
            # Do not abort loading on single invalid value; surface a warning
            # and skip the offending update.
            console.print(
                Text("Warning: ignoring invalid configuration value for ")
                + Text(f"{section}.{setting}", style="magenta")
                + Text(" from ")
                + Text(source, style="cyan")
                + Text(f": {exc}", style="yellow")
            )
            return

        # Merge binary_extensions with defaults instead of replacing
        if section == "scan" and setting == "binary_extensions":
            normalized = self._merge_binary_extensions(current_value, normalized)

        new_section = replace(section_obj, **{setting: normalized})
        self.config = replace(self.config, **{section: new_section})

        if self.config.core.verbose:
            self._log_config_update(setting, normalized, source)

    @staticmethod
    def _merge_binary_extensions(
        current: tuple[str, ...],
        new: ConfigInput,
    ) -> tuple[str, ...]:
        """Merge new binary extensions with existing ones.

        This ensures that user-provided binary_extensions are added to
        the defaults rather than replacing them entirely, similar to how
        custom_language_mapping works.

        Args:
            current: Current binary extensions tuple.
            new: New binary extensions to add.

        Returns:
            Merged tuple of binary extensions with duplicates removed.
        """
        if not isinstance(new, tuple):
            return current

        # Combine and remove duplicates while preserving order
        combined = current + new
        seen = set()
        result = []
        for ext in combined:
            if ext not in seen:
                seen.add(ext)
                result.append(ext)

        return tuple(result)

    @staticmethod
    def _log_config_update(
        setting: str,
        value: ConfigInput,
        source: str,
    ) -> None:
        """Log configuration update in verbose mode.

        Args:
            setting: Setting name that was updated.
            value: New value.
            source: Source of the update.
        """
        console.print(
            Text(f"Updated config from {source}: ")
            + Text(setting, style="magenta")
            + Text(" - ")
            + Text(str(value), style="cyan")
        )
