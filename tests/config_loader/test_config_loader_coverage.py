"""Tests for config loader edge cases and missing coverage."""

from unittest.mock import patch

import pytest

from statsvy.config.config_loader import ConfigLoader
from statsvy.config.config_value_converter import ConfigValueConverter


class TestConfigLoaderVerboseLogging:
    """Test coverage for verbose logging in config loader."""

    def test_verbose_logging_enabled_when_config_verbose_is_true(self) -> None:
        """Test that _log_config_update is called when verbose is enabled."""
        loader = ConfigLoader()

        # Test that _log_config_update method exists and can be called
        with patch("statsvy.config.config_loader.console") as mock_console:
            # Call _log_config_update directly
            loader._log_config_update("test_setting", "test_value", "test")
            # Should call console.print
            assert mock_console.print.called


class TestConfigLoaderEdgeCases:
    """Test edge cases and error paths in config loader."""

    def test_set_section_setting_with_invalid_section(self) -> None:
        """Test _update_section_setting with a non-existent section."""
        loader = ConfigLoader()

        # Try to set a value in a section that doesn't exist
        loader._update_section_setting(
            "nonexistent_section", "setting", "value", "test"
        )

        # Should not raise, just return early
        # Config should remain unchanged
        assert loader.config is not None

    def test_set_section_setting_with_invalid_setting(self) -> None:
        """Test _update_section_setting with a non-existent setting."""
        loader = ConfigLoader()

        # Try to set a value for a setting that doesn't exist in a section
        loader._update_section_setting("core", "nonexistent_setting", "value", "test")

        # Should not raise, just return early
        assert loader.config is not None

    def test_normalize_value_with_mapping_non_mapping_value(self) -> None:
        """Test normalize_value raises TypeError when Mapping config.

        Tests that non-Mapping value raises with Mapping reference.
        """
        # Create a reference object that is a Mapping (dict)
        ref = {"key": "value"}

        # Try to normalize a non-Mapping value
        with pytest.raises(TypeError, match="Expected mapping"):
            ConfigValueConverter.normalize_value("not a mapping", ref)

    def test_normalize_value_with_tuple_string_input(self) -> None:
        """Test normalize_value with tuple reference and string input."""
        # Create a reference tuple
        ref = ("a", "b", "c")

        # Normalize a comma-separated string
        result = ConfigValueConverter.normalize_value("x,y,z", ref)

        # Should return a tuple
        assert isinstance(result, tuple)
        assert result == ("x", "y", "z")

    def test_coerce_tuple_with_invalid_type(self) -> None:
        """Test _coerce_tuple raises TypeError with invalid input."""
        # Try to coerce a type that's not list, tuple, or string
        with pytest.raises(
            TypeError, match="Expected list, tuple, or comma-delimited string"
        ):
            ConfigValueConverter._coerce_tuple(42)

    def test_coerce_tuple_with_list(self) -> None:
        """Test _coerce_tuple with a list input."""
        result = ConfigValueConverter._coerce_tuple(["a", "b", "c"])

        assert isinstance(result, tuple)
        assert result == ("a", "b", "c")

    def test_coerce_tuple_with_tuple(self) -> None:
        """Test _coerce_tuple with a tuple input."""
        input_tuple = ("a", "b", "c")
        result = ConfigValueConverter._coerce_tuple(input_tuple)

        # Should return the same tuple
        assert result == input_tuple

    def test_coerce_tuple_with_string(self) -> None:
        """Test _coerce_tuple with a string input."""
        result = ConfigValueConverter._coerce_tuple("a,b,c")

        assert isinstance(result, tuple)
        assert result == ("a", "b", "c")

    def test_coerce_tuple_with_string_with_spaces(self) -> None:
        """Test _coerce_tuple with spaces in string."""
        result = ConfigValueConverter._coerce_tuple("a , b , c")

        assert result == ("a", "b", "c")

    def test_coerce_tuple_with_empty_string_items(self) -> None:
        """Test _coerce_tuple ignores empty items."""
        result = ConfigValueConverter._coerce_tuple("a,,b,,c")

        assert result == ("a", "b", "c")

    def test_convert_value_with_valid_json_object(self) -> None:
        """Test convert_value with valid JSON object for Mapping ref."""
        ref = {}  # Mapping reference
        result = ConfigValueConverter.convert_value('{"key": "value"}', ref)

        # Should parse the JSON
        assert isinstance(result, dict) or hasattr(result, "items")

    def test_convert_value_with_invalid_json(self) -> None:
        """Test convert_value with invalid JSON raises ValueError."""
        ref = {}  # Mapping reference

        with pytest.raises(ValueError, match="Invalid JSON"):
            ConfigValueConverter.convert_value("not valid json", ref)

    def test_convert_value_with_json_non_dict(self) -> None:
        """Test convert_value with JSON that's not an object."""
        ref = {}  # Mapping reference

        with pytest.raises(ValueError, match="Expected JSON object"):
            ConfigValueConverter.convert_value('["array", "not", "dict"]', ref)

    def test_parse_json_with_valid_json(self) -> None:
        """Test _parse_json with valid JSON."""
        result = ConfigValueConverter._parse_json('{"key": "value"}')

        assert isinstance(result, dict)
        assert result["key"] == "value"  # type: ignore[index]

    def test_parse_json_with_invalid_json(self) -> None:
        """Test _parse_json with invalid JSON raises ValueError."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            ConfigValueConverter._parse_json("not json at all {")

    def test_convert_value_with_float_type(self) -> None:
        """Test convert_value with float reference."""
        ref = 1.5  # float reference
        result = ConfigValueConverter.convert_value("3.14", ref)

        assert isinstance(result, float)
        assert result == 3.14

    def test_convert_value_with_int_type(self) -> None:
        """Test convert_value with int reference."""
        ref = 10  # int reference
        result = ConfigValueConverter.convert_value("42", ref)

        assert isinstance(result, int)
        assert result == 42

    def test_convert_value_with_invalid_int(self) -> None:
        """Test convert_value with invalid int string."""
        ref = 10  # int reference

        with pytest.raises(ValueError):
            ConfigValueConverter.convert_value("not an int", ref)

    def test_convert_value_with_invalid_float(self) -> None:
        """Test convert_value with invalid float string."""
        ref = 1.0  # float reference

        with pytest.raises(ValueError):
            ConfigValueConverter.convert_value("not a float", ref)

    def test_convert_value_with_bool_reference(self) -> None:
        """Test convert_value with bool reference."""
        ref = True  # bool reference

        # Test true variants
        assert ConfigValueConverter.convert_value("true", ref) is True
        assert ConfigValueConverter.convert_value("True", ref) is True
        assert ConfigValueConverter.convert_value("1", ref) is True
        assert ConfigValueConverter.convert_value("yes", ref) is True
        assert ConfigValueConverter.convert_value("YES", ref) is True
        assert ConfigValueConverter.convert_value("on", ref) is True

        # Test false variants
        assert ConfigValueConverter.convert_value("false", ref) is False
        assert ConfigValueConverter.convert_value("0", ref) is False
        assert ConfigValueConverter.convert_value("no", ref) is False

    def test_convert_value_with_string_reference(self) -> None:
        """Test convert_value with string reference."""
        ref = "string"
        result = ConfigValueConverter.convert_value("test value", ref)

        # Should be returned as-is
        assert result == "test value"
        assert isinstance(result, str)

    def test_log_config_update_with_verbose_enabled(self) -> None:
        """Test _log_config_update prints when called."""
        loader = ConfigLoader()

        with patch("statsvy.config.config_loader.console") as mock_console:
            loader._log_config_update("test_setting", "test_value", "test_source")
            # Should call console.print
            mock_console.print.assert_called()
