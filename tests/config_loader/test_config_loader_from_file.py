"""Tests for loading configuration from pyproject.toml."""

import tomllib
from pathlib import Path

import pytest

from statsvy.config.config_loader import ConfigLoader


class TestConfigLoaderFromFile:
    """Test loading configuration from pyproject.toml."""

    def test_load_updates_config_class(self, tmp_path: Path) -> None:
        """Loading should update Config class directly."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.statsvy.core]
verbose = true
default_format = "json"
""")

        loader = ConfigLoader(config_path=config_file)
        loader.load()

        assert loader.config.core.verbose is True
        assert loader.config.core.default_format == "json"

    def test_load_updates_multiple_sections(self, tmp_path: Path) -> None:
        """Should update multiple Config sections."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.statsvy.core]
verbose = true

[tool.statsvy.scan]
max_depth = 5

[tool.statsvy.git]
enabled = false
""")

        loader = ConfigLoader(config_path=config_file)
        loader.load()

        assert loader.config.core.verbose is True
        assert loader.config.scan.max_depth == 5
        assert loader.config.git.enabled is False

    def test_load_preserves_unspecified_values(self, tmp_path: Path) -> None:
        """Unspecified values should keep their defaults."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.statsvy.core]
verbose = true
""")

        loader = ConfigLoader()
        original_color = loader.config.core.color

        loader = ConfigLoader(config_path=config_file)
        loader.load()

        assert loader.config.core.verbose is True
        assert loader.config.core.color == original_color

    def test_load_handles_malformed_toml(self, tmp_path: Path) -> None:
        """Should raise error on malformed TOML."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[tool.statsvy.core\nbroken")

        loader = ConfigLoader(config_path=config_file)
        with pytest.raises(tomllib.TOMLDecodeError):
            loader.load()

    def test_load_with_missing_tool_section(self, tmp_path: Path) -> None:
        """Should handle TOML files without [tool.statsvy] section."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[build-system]
requires = ["setuptools"]
""")

        loader_before = ConfigLoader()
        original_verbose = loader_before.config.core.verbose

        loader = ConfigLoader(config_path=config_file)
        loader.load()

        assert loader.config.core.verbose == original_verbose

    def test_load_ignores_non_dict_values(self, tmp_path: Path) -> None:
        """Should ignore non-dict values in config sections."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.statsvy]
core = "not a dict"
""")

        loader = ConfigLoader(config_path=config_file)
        loader.load()
        pass
