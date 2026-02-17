"""Type conversion utilities for configuration values."""

import json
from collections.abc import Mapping
from types import MappingProxyType
from typing import cast

from statsvy.utils.formatting import parse_size_to_mb

type ConfigScalar = str | bool | int | float
type ConfigMapping = Mapping[str, object]
type ConfigTuple = tuple[str, ...]
type ConfigValue = ConfigScalar | ConfigTuple | ConfigMapping
type ConfigInput = ConfigScalar | ConfigTuple | list[str] | ConfigMapping | None


class ConfigValueConverter:
    """Handles type conversion and coercion for configuration values."""

    @staticmethod
    def _convert_float_value(value: str) -> float:
        """Convert a string to float, accepting human-readable size suffixes.

        Separated to keep `convert_value` simple and reduce cyclomatic
        complexity for the linter.
        """
        try:
            return float(value)
        except ValueError:
            return parse_size_to_mb(value)

    @staticmethod
    def convert_value(value: str, ref: object) -> ConfigValue:
        """Cast a string value to the type of a reference object.

        Used primarily for environment variables which are always strings.

        Args:
            value: The string value to convert.
            ref: The reference object used to determine the target type.

        Returns:
            The value converted to the type of the reference object.

        Raises:
            TypeError: If the value cannot be converted to the reference type.
            ValueError: If JSON parsing fails for mapping types.
        """
        if isinstance(ref, bool):
            converted: ConfigValue = value.lower() in ("true", "1", "yes", "on")
        elif isinstance(ref, int):
            converted = int(value)
        elif isinstance(ref, float):
            converted = ConfigValueConverter._convert_float_value(value)
        elif isinstance(ref, tuple):
            converted = ConfigValueConverter._coerce_tuple(value)
        elif isinstance(ref, Mapping):
            parsed = ConfigValueConverter._parse_json(value)
            if not isinstance(parsed, dict):
                raise ValueError("Expected JSON object for mapping config")
            converted = MappingProxyType(parsed)
        else:
            converted = value
        return cast(ConfigValue, converted)

    @staticmethod
    def normalize_value(value: ConfigInput, ref: object) -> ConfigInput:
        """Normalize a value based on the existing reference type.

        Args:
            value: Value to normalize.
            ref: Reference object for type checking.

        Returns:
            Normalized value.

        Raises:
            TypeError: If value type doesn't match reference type.
        """
        if isinstance(ref, float):
            # Allow numeric values or human-readable size strings for float refs
            if isinstance(value, int | float):
                return float(value)
            if isinstance(value, str):
                return parse_size_to_mb(value)
            raise TypeError("Expected numeric or size string for float config value")

        if isinstance(ref, tuple):
            return cast(ConfigInput, ConfigValueConverter._coerce_tuple(value))
        if isinstance(ref, Mapping):
            if isinstance(value, Mapping):
                return cast(ConfigInput, MappingProxyType(dict(value.items())))
            raise TypeError("Expected mapping for config update")
        return value

    @staticmethod
    def _coerce_tuple(value: object) -> tuple[str, ...] | tuple[object, ...]:
        """Coerce list or comma-delimited strings into a tuple of strings.

        Args:
            value: Value to coerce to tuple.

        Returns:
            Tuple representation of the value.

        Raises:
            TypeError: If value cannot be coerced to tuple.
        """
        if isinstance(value, tuple):
            return value
        if isinstance(value, list):
            return tuple(str(item) for item in value)
        if isinstance(value, str):
            return tuple(item.strip() for item in value.split(",") if item.strip())
        raise TypeError("Expected list, tuple, or comma-delimited string")

    @staticmethod
    def _parse_json(value: str) -> object:
        """Parse a JSON string to a Python object.

        Args:
            value: JSON string to parse.

        Returns:
            Parsed Python object.

        Raises:
            ValueError: If JSON parsing fails.
        """
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON for config value: {value}") from exc
