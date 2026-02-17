"""Tests for _update_config method."""

from pathlib import Path

from statsvy.config.config_loader import ConfigLoader


class TestConfigLoaderUpdateConfig:
    """Tests for _update_config method."""

    def test_update_config_ignores_invalid_sections(self, tmp_path: Path) -> None:
        """Test that _update_config ignores sections not in Config class.

        When the config dict contains a section that doesn't exist in Config,
        it should be skipped (continue) without raising an error.
        """
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.statsvy.nonexistent_section]
some_key = "some_value"

[tool.statsvy.core]
verbose = true
""")

        loader = ConfigLoader(config_path=config_file)
        loader.load()

        assert loader.config.core.verbose is True
