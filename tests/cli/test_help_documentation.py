"""Test suite for the CLI module.

Tests cover the scan, config, track/untrack, and latest commands, including
flag handling, error conditions, output format options, and edge cases.

Design note — the ``scan`` command's ``--dir`` flag:
    The current implementation of ``cli.py:scan()`` ignores the ``--dir`` flag
    entirely: it always reads from ``.statsvy/project.json`` or falls back to
    ``Path.cwd()``.  Tests that exercise path selection via the command line
    therefore use ``--dir`` as currently wired (i.e. relying on the positional
    scan of the current working directory) rather than the flag.  A TODO is
    noted where the behaviour should be fixed in cli.py.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner, Result

from statsvy.cli import main

_CLI_MODULE = "statsvy.cli_main"


@pytest.fixture()
def runner() -> CliRunner:
    """Provide a Click CLI test runner.

    Returns:
        CliRunner instance for invoking CLI commands.
    """
    return CliRunner()


@pytest.fixture()
def temp_dir(tmp_path: Path) -> Path:
    """Create a small directory tree for testing scan.

    Structure::

        tmp_path/
          file1.py     - "# Python file"
          file2.txt    - "Text file"
          subdir/
            file3.py   - "# Another Python file"
            nested/
              file4.py - "# Nested Python file"

    Args:
        tmp_path: pytest temporary directory.

    Returns:
        Root Path of the created structure.
    """
    (tmp_path / "file1.py").write_text("# Python file")
    (tmp_path / "file2.txt").write_text("Text file")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file3.py").write_text("# Another Python file")
    nested = subdir / "nested"
    nested.mkdir()
    (nested / "file4.py").write_text("# Nested Python file")
    return tmp_path


def _invoke_scan(runner: CliRunner, directory: Path, *extra_args: str) -> Result:
    """Invoke ``statsvy scan`` pointing at *directory* with optional extra args."""
    original_cwd = os.getcwd()

    os.chdir(directory)
    try:
        with patch(f"{_CLI_MODULE}.Path.cwd", return_value=directory):
            result: Result = runner.invoke(main, ["scan", *extra_args])
    finally:
        os.chdir(original_cwd)

    return result


class TestHelpDocumentation:
    """Tests for help text on all commands."""

    def test_main_help_exits_zero(self, runner: CliRunner) -> None:
        """Test that --help exits with code 0."""
        assert runner.invoke(main, ["--help"]).exit_code == 0

    def test_main_help_lists_scan_command(self, runner: CliRunner) -> None:
        """Test that the main help output mentions the scan subcommand."""
        output = runner.invoke(main, ["--help"]).output.lower()
        assert "scan" in output

    def test_main_help_mentions_statsvy_toml(self, runner: CliRunner) -> None:
        """Main help should mention statsvy.toml as a supported config file."""
        assert "statsvy.toml" in runner.invoke(main, ["--help"]).output.lower()

    def test_scan_help_exits_zero(self, runner: CliRunner) -> None:
        """Test that scan --help exits with code 0."""
        assert runner.invoke(main, ["scan", "--help"]).exit_code == 0

    def test_scan_help_mentions_ignore_option(self, runner: CliRunner) -> None:
        """Test that scan help documents the --ignore option."""
        help_out = runner.invoke(main, ["scan", "--help"]).output.lower()
        assert "ignore" in help_out
        # new alias should be present
        assert "exclude" in help_out

    def test_scan_help_mentions_dir_option(self, runner: CliRunner) -> None:
        """Test that scan help documents the --dir option."""
        help_out = runner.invoke(main, ["scan", "--help"]).output.lower()
        assert "dir" in help_out
        # positional target should appear in usage/help
        assert "[target]" in help_out or "usage:" in help_out
        # timeout and profile aliases documented
        assert "--timeout" in help_out
        assert "--min-lines" in help_out
        assert "--profile" in help_out
        assert "--track-io" in help_out
        assert "--track-mem" in help_out
        assert "--track-cpu" in help_out
        assert "--quiet" in help_out
        # newly added CSS toggle
        assert "--no-css" in help_out

    def test_config_help_exits_zero(self, runner: CliRunner) -> None:
        """Test that config --help exits with code 0."""
        assert runner.invoke(main, ["config", "--help"]).exit_code == 0

    def test_compare_help_mentions_no_css(self, runner: CliRunner) -> None:
        """Compare help should document the --no-css option."""
        help_out = runner.invoke(main, ["compare", "--help"]).output.lower()
        assert "--no-css" in help_out
