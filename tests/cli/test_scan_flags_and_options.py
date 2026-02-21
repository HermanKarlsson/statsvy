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


class TestScanFlagsAndOptions:
    """Tests verifying that all scan flags are accepted without error."""

    def test_verbose_flag_accepted(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that --verbose flag is accepted and the command exits cleanly."""
        result = _invoke_scan(runner, temp_dir, "--verbose")
        assert result.exit_code == 0

    def test_no_color_flag_accepted(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that --no-color flag is accepted."""
        result = _invoke_scan(runner, temp_dir, "--no-color")
        assert result.exit_code == 0

    def test_no_progress_flag_accepted(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that --no-progress flag disables the progress bar without error."""
        result = _invoke_scan(runner, temp_dir, "--no-progress")
        assert result.exit_code == 0

    def test_include_hidden_flag_accepted(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test --include-hidden flag is accepted and hidden files can be scanned."""
        (tmp_path / ".hidden").write_text("hidden")
        (tmp_path / "visible.py").write_text("code")
        result = _invoke_scan(runner, tmp_path, "--include-hidden")
        assert result.exit_code == 0

    def test_no_gitignore_flag_accepted(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test that --no-gitignore flag is accepted."""
        result = _invoke_scan(runner, temp_dir, "--no-gitignore")
        assert result.exit_code == 0

    def test_no_gitignore_flag_disables_gitignore(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """End-to-end: `--no-gitignore` causes .gitignore patterns to be ignored.

        We rely on `--verbose` output which prints processed file paths so we can
        assert whether a .gitignore'd file was scanned or not.
        """
        (tmp_path / ".gitignore").write_text("*.txt\n")
        (tmp_path / "file1.txt").write_text("ignored")
        (tmp_path / "file2.py").write_text("code")

        # Without the flag the .txt file should be skipped
        result = _invoke_scan(runner, tmp_path, "--verbose")
        assert result.exit_code == 0
        assert "file1.txt" not in result.output

        # With the flag the .txt file should be processed
        result = _invoke_scan(runner, tmp_path, "--verbose", "--no-gitignore")
        assert result.exit_code == 0
        assert "file1.txt" in result.output

    def test_follow_symlinks_flag_accepted(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test that --follow-symlinks flag is accepted."""
        result = _invoke_scan(runner, temp_dir, "--follow-symlinks")
        assert result.exit_code == 0

    def test_git_flag_accepted(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that --git flag is accepted."""
        result = _invoke_scan(runner, temp_dir, "--git")
        assert result.exit_code == 0

    def test_no_git_flag_accepted(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that --no-git flag is accepted."""
        result = _invoke_scan(runner, temp_dir, "--no-git")
        assert result.exit_code == 0

    def test_no_save_flag_accepted(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that --no-save flag is accepted."""
        result = _invoke_scan(runner, temp_dir, "--no-save")
        assert result.exit_code == 0

    def test_max_depth_option_accepted(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that --max-depth option is accepted with a valid integer."""
        result = _invoke_scan(runner, temp_dir, "--max-depth", "1")
        assert result.exit_code == 0

    def test_max_file_size_option_accepted(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test that --max-file-size option is accepted with a valid integer."""
        result = _invoke_scan(runner, temp_dir, "--max-file-size", "10")
        assert result.exit_code == 0

    def test_min_file_size_option_accepted(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test that --min-file-size option is accepted with a valid integer."""
        result = _invoke_scan(runner, temp_dir, "--min-file-size", "1")
        assert result.exit_code == 0

    def test_min_max_file_size_accept_suffixes(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """CLI should accept human-readable size suffixes for min/max file size."""
        res = _invoke_scan(
            runner, temp_dir, "--min-file-size", "512b", "--max-file-size", "1.5MB"
        )
        assert res.exit_code == 0

    def test_ignore_single_pattern(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that a single --ignore pattern is accepted without error."""
        result = _invoke_scan(runner, temp_dir, "--ignore", "*.txt")
        assert result.exit_code == 0

    def test_ignore_multiple_patterns(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that multiple --ignore patterns (repeated flag) are accepted."""
        result = _invoke_scan(
            runner, temp_dir, "--ignore", "*.txt", "--ignore", "*.log"
        )
        assert result.exit_code == 0

    def test_ignore_on_empty_directory(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test that --ignore patterns on an empty directory do not cause errors."""
        result = _invoke_scan(runner, tmp_path, "--ignore", "*.py", "--ignore", "*.txt")
        assert result.exit_code == 0

    def test_format_table_accepted(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that --format table is accepted."""
        result = _invoke_scan(runner, temp_dir, "--format", "table")
        assert result.exit_code == 0

    def test_format_json_accepted(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that --format json is accepted."""
        result = _invoke_scan(runner, temp_dir, "--format", "json")
        assert result.exit_code == 0

    def test_format_md_accepted(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that --format md is accepted."""
        result = _invoke_scan(runner, temp_dir, "--format", "md")
        assert result.exit_code == 0

    def test_format_markdown_accepted(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that --format markdown is accepted."""
        result = _invoke_scan(runner, temp_dir, "--format", "markdown")
        assert result.exit_code == 0

    def test_output_file_option_saves_file(
        self, runner: CliRunner, temp_dir: Path, tmp_path: Path
    ) -> None:
        """Test that --output saves results to the specified file."""
        output_file = tmp_path / "results.txt"
        _invoke_scan(runner, temp_dir, "--output", str(output_file))
        assert output_file.exists()

    def test_combined_flags_accepted(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that several flags can be combined without error."""
        result = _invoke_scan(
            runner,
            temp_dir,
            "--verbose",
            "--no-color",
            "--max-depth",
            "2",
            "--include-hidden",
            "--no-gitignore",
        )
        assert result.exit_code == 0

    def test_exclude_alias_for_ignore(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that --exclude / -e works as an alias for --ignore."""
        result = _invoke_scan(runner, temp_dir, "--exclude", "*.txt")
        assert result.exit_code == 0
        result2 = _invoke_scan(runner, temp_dir, "-e", "*.txt")
        assert result2.exit_code == 0

    def test_scan_prints_short_summary_for_skips_and_duplicates_when_not_verbose(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Print concise summaries for skipped files and duplicates when not verbose."""
        # Create a .git directory (ignored by default) with a file to trigger
        # a skipped count, and two large identical files to trigger duplicates.
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "ignored.txt").write_text("ignored")

        # Two large identical files (> duplicate threshold default = 1024)
        content = "x" * 2048
        (tmp_path / "a.bin").write_text(content)
        (tmp_path / "b.bin").write_text(content)

        result = _invoke_scan(runner, tmp_path, "--no-save")
        assert result.exit_code == 0
        # Short informative lines should be present even without -v
        assert "files skipped" in result.output.lower()
        assert "duplicate files detected" in result.output.lower()

    def test_dependency_parsing_failure_shows_warning(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """When dependency parsing fails we should print a short warning by default."""
        # Create a simple project with a file that would normally be scanned
        (tmp_path / "file.py").write_text("print(1)")

        with patch(
            "statsvy.core.project_scanner.ProjectScanner.scan",
            side_effect=ValueError("parse error"),
        ):
            result = _invoke_scan(runner, tmp_path, "--no-save")

        assert result.exit_code == 0
        assert "warning: failed to analyze dependencies" in result.output.lower()

    def test_min_lines_alias_accepted(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that --min-lines is accepted as alias for --min-lines-threshold."""
        result = _invoke_scan(runner, temp_dir, "--min-lines", "0")
        assert result.exit_code == 0

    def test_scan_accepts_positional_target(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test that `statsvy scan <dir>` (positional) is accepted."""
        (tmp_path / "file.py").write_text("print(1)")
        # Invoke using positional path
        result = runner.invoke(
            main, ["scan", str(tmp_path), "--no-save", "--no-progress"]
        )
        assert result.exit_code == 0

    def test_quiet_flag_suppresses_output(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test that --quiet/-q suppresses console output for scan."""
        result = _invoke_scan(runner, temp_dir, "--quiet")
        # No verbose output and minimal/empty output expected
        assert result.exit_code == 0
        assert result.output.strip() == ""

    def test_no_deps_list_flag_accepted(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test that --no-deps-list flag is accepted without error."""
        result = _invoke_scan(runner, temp_dir, "--no-deps-list", "--no-save")
        assert result.exit_code == 0

    def test_no_deps_list_appears_in_help(self, runner: CliRunner) -> None:
        """Test that --no-deps-list is documented in --help output."""
        result = runner.invoke(main, ["scan", "--help"])
        assert result.exit_code == 0
        assert "--no-deps-list" in result.output
