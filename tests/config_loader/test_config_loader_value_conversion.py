"""Tests for value type conversion and integration."""

from pathlib import Path

import pytest

from statsvy.config.config_loader import ConfigLoader
from statsvy.config.config_value_converter import ConfigValueConverter


class TestConfigLoaderValueConversion:
    """Tests for value type conversion from environment variables."""

    def test_convert_value_float_type(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test converting string to float type.

        When _convert_value receives a float reference value,
        it should convert the string to float.
        """
        monkeypatch.setenv("STATSVY_CORE_TIMEOUT", "3.5")

        loader = ConfigLoader()
        loader.load()
        pass

    def test_convert_value_returns_correct_type(self) -> None:
        """Test that convert_value returns values with correct type."""
        # Ignore warnings for testing purposes

        bool_result = ConfigValueConverter.convert_value("true", True)
        assert isinstance(bool_result, bool)
        assert bool_result is True

        int_result = ConfigValueConverter.convert_value("42", 0)
        assert isinstance(int_result, int)
        assert int_result == 42

        float_result = ConfigValueConverter.convert_value("3.14", 0.0)
        assert isinstance(float_result, float)
        assert float_result == 3.14

    def test_convert_value_string_default_behavior(self) -> None:
        """Test default behavior for string type conversion.

        When reference type is str, the function should return the string as-is.
        """
        result = ConfigValueConverter.convert_value("value.with.dots", "")
        assert isinstance(result, str)
        assert result == "value.with.dots"

    def test_typical_usage_pattern(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test typical usage: load file, env, then CLI."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.statsvy.core]
verbose = false
default_format = "table"

[tool.statsvy.scan]
max_depth = 5
""")

        monkeypatch.setenv("STATSVY_CORE_VERBOSE", "true")

        loader = ConfigLoader(config_path=config_file)
        loader.load()

        loader.update_from_cli(scan_max_depth=10)

        assert loader.config.core.verbose is True
        assert loader.config.core.default_format == "table"
        assert loader.config.scan.max_depth == 10

    def test_reset_not_needed_between_loads(self) -> None:
        """Config can be loaded multiple times without reset."""
        loader = ConfigLoader()
        loader.update_from_cli(core_verbose=True)
        assert loader.config.core.verbose is True

        loader.update_from_cli(core_verbose=False)
        assert loader.config.core.verbose is False

    def test_multiple_loader_instances(self) -> None:
        """Multiple ConfigLoader instances have independent config state."""
        loader1 = ConfigLoader()
        loader1.update_from_cli(core_verbose=True)

        loader2 = ConfigLoader()
        # Each loader has its own config instance starting from defaults
        assert loader2.config.core.verbose is False
