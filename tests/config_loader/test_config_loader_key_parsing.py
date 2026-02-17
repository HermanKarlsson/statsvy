"""Tests for configuration key parsing."""

from statsvy.config.config_loader import ConfigLoader


class TestConfigLoaderKeyParsing:
    """Tests for configuration key parsing."""

    def test_parse_config_key_valid_format(self) -> None:
        """Test parsing valid config key format."""
        loader = ConfigLoader()
        # Ignore warning for testing purposes
        section, setting = loader._parse_config_key("core_verbose")
        assert section == "core"
        assert setting == "verbose"

    def test_parse_config_key_returns_none_for_invalid_format(self) -> None:
        """Test that invalid key format returns None, None.

        When a key doesn't contain an underscore, _parse_config_key
        should return (None, None) to indicate parsing failure.
        """
        loader = ConfigLoader()
        # Ignore warning for testing purposes
        section, setting = loader._parse_config_key("invalidkey")
        assert section is None
        assert setting is None

    def test_parse_config_key_with_multiple_underscores(self) -> None:
        """Test parsing key with multiple underscores."""
        loader = ConfigLoader()
        # Ignore warning for testing purposes
        section, setting = loader._parse_config_key("core_verbose_mode_enabled")
        assert section == "core"
        assert setting == "verbose_mode_enabled"
