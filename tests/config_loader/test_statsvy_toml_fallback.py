"""Tests for fallback TOML configuration file `statsvy.toml`.

These tests verify that `ConfigLoader` will use `statsvy.toml` when
`pyproject.toml` is not present, and that `pyproject.toml` keeps higher
priority when both files exist.
"""

from pathlib import Path
from unittest.mock import patch

from statsvy.config.config_loader import ConfigLoader


class TestStatsvyTomlFallback:
    """Unit tests for statsvy.toml fallback behaviour."""

    def test_init_prefers_statsvy_when_pyproject_missing(self, tmp_path: Path) -> None:
        """Default loader should pick `statsvy.toml` if no pyproject exists."""
        (tmp_path / "statsvy.toml").write_text(
            """
[tool.statsvy.core]
verbose = true
"""
        )

        with patch("statsvy.config.config_loader.Path.cwd", return_value=tmp_path):
            loader = ConfigLoader()

        assert loader.config_path == tmp_path / "statsvy.toml"

    def test_load_reads_statsvy_toml_by_default(self, tmp_path: Path) -> None:
        """Loader should read configuration from `statsvy.toml` when present."""
        (tmp_path / "statsvy.toml").write_text(
            """
[tool.statsvy.core]
verbose = true
"""
        )

        with patch("statsvy.config.config_loader.Path.cwd", return_value=tmp_path):
            loader = ConfigLoader()
            loader.load()

        assert loader.config.core.verbose is True

    def test_explicit_config_path_accepts_statsvy_toml(self, tmp_path: Path) -> None:
        """Passing `config_path` explicitly should accept a statsvy.toml path."""
        cfg = tmp_path / "statsvy.toml"
        cfg.write_text(
            """
[tool.statsvy.core]
default_format = "json"
"""
        )

        loader = ConfigLoader(config_path=cfg)
        loader.load()

        assert loader.config.core.default_format == "json"

    def test_prefers_pyproject_over_statsvy_when_both_present(
        self, tmp_path: Path
    ) -> None:
        """When both files exist the loader should prefer `pyproject.toml`."""
        (tmp_path / "pyproject.toml").write_text(
            """
[tool.statsvy.core]
default_format = "table"
"""
        )
        (tmp_path / "statsvy.toml").write_text(
            """
[tool.statsvy.core]
default_format = "json"
"""
        )

        with patch("statsvy.config.config_loader.Path.cwd", return_value=tmp_path):
            loader = ConfigLoader()
            loader.load()

        assert loader.config.core.default_format == "table"
