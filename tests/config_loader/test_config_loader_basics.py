"""Tests for basic ConfigLoader functionality."""

from pathlib import Path

from statsvy.config.config_loader import ConfigLoader


class TestConfigLoaderBasics:
    """Test basic ConfigLoader functionality."""

    def test_init_with_default_path(self) -> None:
        """ConfigLoader should use current dir by default."""
        loader = ConfigLoader()
        assert loader.config_path == Path.cwd() / "pyproject.toml"

    def test_init_with_custom_path(self, tmp_path: Path) -> None:
        """ConfigLoader should accept custom path."""
        config_file = tmp_path / "custom.toml"
        loader = ConfigLoader(config_path=config_file)
        assert loader.config_path == config_file

    def test_loader_has_config_instance(self) -> None:
        """ConfigLoader should have a Config instance."""
        loader = ConfigLoader()
        assert loader.config is not None

    def test_load_missing_file_keeps_defaults(self, tmp_path: Path) -> None:
        """Loading non-existent file should keep Config defaults."""
        missing_file = tmp_path / "nonexistent.toml"
        loader = ConfigLoader(config_path=missing_file)
        original_verbose = loader.config.core.verbose
        loader.load()
        assert loader.config.core.verbose == original_verbose
