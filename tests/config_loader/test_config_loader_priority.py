"""Tests for configuration priority order: CLI > ENV > FILE > DEFAULTS."""

from pathlib import Path

import pytest

from statsvy.config.config_loader import ConfigLoader


class TestConfigLoaderPriority:
    """Test priority order: CLI > ENV > FILE > DEFAULTS."""

    def test_priority_file_over_defaults(self, tmp_path: Path) -> None:
        """File config should override defaults."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.statsvy.core]
verbose = true
""")

        loader = ConfigLoader(config_path=config_file)
        loader.load()

        assert loader.config.core.verbose is True

    def test_priority_env_over_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ENV vars should override file config."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.statsvy.core]
verbose = false
""")

        monkeypatch.setenv("STATSVY_CORE_VERBOSE", "true")

        loader = ConfigLoader(config_path=config_file)
        loader.load()

        assert loader.config.core.verbose is True

    def test_priority_cli_over_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI args should override ENV vars."""
        monkeypatch.setenv("STATSVY_CORE_VERBOSE", "true")

        loader = ConfigLoader()
        loader.load()

        loader.update_from_cli(core_verbose=False)

        assert loader.config.core.verbose is False

    def test_priority_full_chain(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test complete priority chain."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.statsvy.core]
verbose = false
color = false
""")

        monkeypatch.setenv("STATSVY_CORE_VERBOSE", "true")

        loader = ConfigLoader(config_path=config_file)
        loader.load()

        loader.update_from_cli(core_verbose=False)

        assert loader.config.core.verbose is False
        assert loader.config.core.color is False
