"""Configuration loading and merge coordination."""

from dataclasses import replace
from pathlib import Path
from typing import TypeVar

from rich.text import Text

from statsvy.config.config_env_reader import ConfigEnvReader
from statsvy.config.config_file_reader import ConfigFileReader
from statsvy.config.config_value_converter import (
    ConfigInput,
    ConfigValueConverter,
)
from statsvy.data.config import Config
from statsvy.utils.console import console

_SectionT = TypeVar("_SectionT")


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

        This method delegates the heavy-lifting to focused helper methods so
        complexity and branching are easier to test and reason about.
        """
        section_obj = getattr(self.config, section, None)
        if section_obj is None:
            return

        # Try direct attribute update (e.g. `core.verbose`). If handled,
        # stop further processing.
        if self._try_update_direct_setting(
            section, section_obj, setting, value, source
        ):
            return

        # Try nested update (format: <nested>_<setting>), e.g.:
        # `core.performance_track_mem` -> core.performance.track_mem
        if self._try_update_nested_setting(
            section, section_obj, setting, value, source
        ):
            return

        # Legacy mapping for old `core.track_performance` key.
        if section == "core" and setting == "track_performance":
            self._handle_legacy_track_performance(section, section_obj, value, source)
            return

        # Unknown setting — ignore silently
        return

    def _try_update_direct_setting(
        self,
        section: str,
        section_obj: _SectionT,
        setting: str,
        value: ConfigInput,
        source: str,
    ) -> bool:
        """Attempt to update a top-level attribute on *section_obj*.

        Returns True when the key was recognised and handled (whether or not
        the update succeeded). Returns False if the setting does not exist
        on *section_obj* so callers can try other handlers.
        """
        if not hasattr(section_obj, setting):
            return False

        current_value = getattr(section_obj, setting)
        try:
            normalized = ConfigValueConverter.normalize_value(value, current_value)
        except (TypeError, ValueError) as exc:
            console.print(
                Text("Warning: ignoring invalid configuration value for ")
                + Text(f"{section}.{setting}", style="magenta")
                + Text(" from ")
                + Text(source, style="cyan")
                + Text(f": {exc}", style="yellow")
            )
            return True

        # Special-case merge for binary_extensions
        if section == "scan" and setting == "binary_extensions":
            normalized = self._merge_binary_extensions(current_value, normalized)

        self._replace_section(section, **{setting: normalized})
        if self.config.core.verbose:
            self._log_config_update(setting, normalized, source)
        return True

    def _try_update_nested_setting(
        self,
        section: str,
        section_obj: _SectionT,
        setting: str,
        value: ConfigInput,
        source: str,
    ) -> bool:
        """Handle nested updates in the format `<nested>_<setting>`.

        Returns True when handled, False otherwise.
        """
        if "_" not in setting:
            return False

        nested, nested_setting = setting.split("_", 1)
        if not hasattr(section_obj, nested):
            return False

        nested_obj = getattr(section_obj, nested)
        if not hasattr(nested_obj, nested_setting):
            return False

        current_value = getattr(nested_obj, nested_setting)
        try:
            normalized = ConfigValueConverter.normalize_value(value, current_value)
        except (TypeError, ValueError) as exc:
            console.print(
                Text("Warning: ignoring invalid configuration value for ")
                + Text(f"{section}.{setting}", style="magenta")
                + Text(" from ")
                + Text(source, style="cyan")
                + Text(f": {exc}", style="yellow")
            )
            return True

        new_nested = replace(nested_obj, **{nested_setting: normalized})
        self._replace_section(section, **{nested: new_nested})
        if self.config.core.verbose:
            self._log_config_update(setting, normalized, source)
        return True

    def _handle_legacy_track_performance(
        self, section: str, section_obj: _SectionT, value: ConfigInput, source: str
    ) -> bool:
        """Map legacy `core.track_performance` to new performance flags.

        Updates `core.performance.track_mem` and
        `core.performance.track_io` for backward compatibility.
        """
        perf_obj = getattr(section_obj, "performance", None)
        if perf_obj is None or not hasattr(perf_obj, "track_mem"):
            return False

        normalized = ConfigValueConverter.normalize_value(value, perf_obj.track_mem)
        new_perf = replace(perf_obj, track_mem=normalized, track_io=normalized)
        # Update the statically-typed `core` section so replace() receives a
        # concrete dataclass instance (avoids type-checker complaints).
        new_section = replace(self.config.core, performance=new_perf)
        self.config = replace(self.config, **{section: new_section})
        if self.config.core.verbose:
            self._log_config_update("track_performance", normalized, source)
        return True

    def _replace_section(self, section: str, **updates: ConfigInput) -> None:
        """Replace a top-level config section using dataclasses.replace.

        Args:
            section: Section name (e.g. ``core``, ``scan``).
            **updates: Field updates applied to the selected section.

        Raises:
            AssertionError: If section name is unknown.
        """
        sections = {
            "core": self.config.core,
            "scan": self.config.scan,
            "language": self.config.language,
            "storage": self.config.storage,
            "git": self.config.git,
            "display": self.config.display,
            "comparison": self.config.comparison,
            "dependencies": self.config.dependencies,
            "files": self.config.files,
        }
        section_obj = sections.get(section)
        if section_obj is None:
            raise AssertionError(f"Unhandled config section: {section}")

        new_section = replace(section_obj, **updates)
        self.config = replace(self.config, **{section: new_section})

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
