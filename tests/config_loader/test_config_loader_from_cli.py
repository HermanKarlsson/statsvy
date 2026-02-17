"""Tests for updating configuration from CLI arguments."""

from statsvy.config.config_loader import ConfigLoader


class TestConfigLoaderFromCLI:
    """Test updating from CLI arguments."""

    def test_update_from_cli_updates_config(self) -> None:
        """CLI arguments should update Config."""
        loader = ConfigLoader()
        loader.update_from_cli(core_verbose=True, scan_max_depth=10)
        assert loader.config.core.verbose is True
        assert loader.config.scan.max_depth == 10

    def test_update_from_cli_ignores_none_values(self) -> None:
        """None values should not update Config."""
        loader = ConfigLoader()
        original_verbose = loader.config.core.verbose
        loader.update_from_cli(core_verbose=None, core_color=False)
        assert loader.config.core.verbose == original_verbose
        assert loader.config.core.color is False

    def test_update_from_cli_handles_invalid_keys(self) -> None:
        """Should ignore invalid CLI argument keys."""
        loader = ConfigLoader()
        loader.update_from_cli(invalid_key=True)
        pass

    def test_update_from_cli_skips_malformed_keys(self) -> None:
        """Should skip keys without underscore separator."""
        loader = ConfigLoader()
        loader.update_from_cli(invalidkey=True)
        pass

    def test_update_from_cli_with_invalid_section(self) -> None:
        """Should ignore updates for non-existent sections."""
        loader = ConfigLoader()
        loader.update_from_cli(nonexistent_key=True)
        pass

    def test_update_from_cli_with_invalid_setting(self) -> None:
        """Should ignore updates for non-existent settings in valid sections."""
        loader = ConfigLoader()
        loader.update_from_cli(core_nonexistent=True)
        pass

    def test_update_from_cli_various_types(self) -> None:
        """Should handle various value types from CLI."""
        loader = ConfigLoader()
        loader.update_from_cli(
            core_verbose=True,
            scan_max_depth=10,
            core_default_format="json",
        )
        assert loader.config.core.verbose is True
        assert loader.config.scan.max_depth == 10
        assert loader.config.core.default_format == "json"
