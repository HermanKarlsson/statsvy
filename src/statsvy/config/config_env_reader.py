"""Environment variable reading utilities for configuration."""

import os
from typing import Any

from statsvy.config.config_value_converter import ConfigValueConverter
from statsvy.data.config import Config


class ConfigEnvReader:
    """Reads configuration from environment variables."""

    @staticmethod
    def read_env_overrides(config: Config) -> dict[str, dict[str, Any]]:
        """Extract configuration overrides from environment variables.

        Looks for environment variables starting with 'STATSVY_'.
        Format: STATSVY_SECTION_KEY (e.g., STATSVY_CORE_VERBOSE).

        Args:
            config: Current Config instance to determine types.

        Returns:
            Dictionary mapping section names to their setting updates.
        """
        overrides: dict[str, dict[str, Any]] = {}

        for env_key, env_value in os.environ.items():
            if not env_key.startswith("STATSVY_"):
                continue

            parts = env_key.replace("STATSVY_", "").lower().split("_", 1)
            if len(parts) != 2:
                continue

            section, key = parts

            # Validate section exists
            if not hasattr(config, section):
                continue

            section_obj = getattr(config, section)

            # Validate key exists in section
            if not hasattr(section_obj, key):
                continue

            # Convert value based on current type
            current_value = getattr(section_obj, key)
            converted = ConfigValueConverter.convert_value(env_value, current_value)

            # Store override
            if section not in overrides:
                overrides[section] = {}
            overrides[section][key] = converted

        return overrides
