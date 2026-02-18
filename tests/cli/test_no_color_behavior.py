"""Tests for the --no-color CLI flag and runtime console colour toggling."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from statsvy.cli import main
from statsvy.utils.console import console as app_console


@pytest.fixture()
def runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


class TestNoColorBehavior:
    """Tests for the --no-color CLI flag and runtime console colour toggling."""

    def test_console_color_default_true(self) -> None:
        """By default the shared console should have colours enabled."""
        assert getattr(app_console, "_color_enabled", True) is True

    def test_no_color_disables_console_color(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Running `scan --no-color` should update runtime console to disable colour."""
        # create a very small project directory to scan
        (tmp_path / "file.py").write_text("print(1)")

        result = runner.invoke(
            main, ["scan", str(tmp_path), "--no-color", "--no-save", "--no-progress"]
        )
        assert result.exit_code == 0

        # console wrapper reflects the setting
        assert getattr(app_console, "_color_enabled", True) is False
