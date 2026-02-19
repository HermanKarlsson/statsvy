"""Test suite for --no-save flag behavior.

Tests verify that the --no-save flag prevents scan results from being
saved to history, while the default behavior (or --save) does save them.
"""

import json
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
def scan_dir(tmp_path: Path) -> Path:
    """Create a minimal directory structure for scanning.

    Structure::

        tmp_path/
          .statsvy/          - Stats directory (ready for history)
          test_file.py       - "# Test Python file"

    Args:
        tmp_path: pytest temporary directory.

    Returns:
        Root Path of the created structure.
    """
    # Create .statsvy directory for storage
    statsvy_dir = tmp_path / ".statsvy"
    statsvy_dir.mkdir()

    # Create a test file to scan
    (tmp_path / "test_file.py").write_text("# Test Python file")

    return tmp_path


def _invoke_scan(runner: CliRunner, directory: Path, *extra_args: str) -> Result:
    """Invoke ``statsvy scan`` in the given directory with optional extra args.

    Args:
        runner: Click CLI test runner.
        directory: Directory to scan from (sets as cwd).
        *extra_args: Additional command-line arguments.

    Returns:
        Result object from the CLI invocation.
    """
    original_cwd = os.getcwd()

    os.chdir(directory)
    try:
        with patch(f"{_CLI_MODULE}.Path.cwd", return_value=directory):
            result: Result = runner.invoke(main, ["scan", *extra_args])
    finally:
        os.chdir(original_cwd)

    return result


class TestNoSaveBehavior:
    """Tests verifying --no-save flag prevents history from being saved."""

    def test_no_save_prevents_history_creation(
        self, runner: CliRunner, scan_dir: Path
    ) -> None:
        """Test that --no-save flag prevents history.json from being created."""
        history_file = scan_dir / ".statsvy" / "history.json"

        # Ensure history doesn't exist initially
        assert not history_file.exists()

        # Run scan with --no-save
        result = _invoke_scan(runner, scan_dir, "--no-save")

        # Verify scan succeeded
        assert result.exit_code == 0

        # Verify history was NOT created
        assert not history_file.exists()

    def test_no_save_prevents_history_file_updates(
        self, runner: CliRunner, scan_dir: Path
    ) -> None:
        """Test that --no-save does not append to existing history.json."""
        history_file = scan_dir / ".statsvy" / "history.json"

        # Create initial history with one entry
        history_file.write_text('[{"time": "2024-01-01 12:00:00", "metrics": {}}]')
        initial_content = history_file.read_text()

        # Run scan with --no-save
        result = _invoke_scan(runner, scan_dir, "--no-save")

        # Verify scan succeeded
        assert result.exit_code == 0

        # Verify history was NOT modified
        assert history_file.read_text() == initial_content

    def test_no_save_with_other_flags_works(
        self, runner: CliRunner, scan_dir: Path
    ) -> None:
        """Test that --no-save can be combined with other flags."""
        history_file = scan_dir / ".statsvy" / "history.json"

        # Run scan with multiple flags including --no-save
        result = _invoke_scan(
            runner,
            scan_dir,
            "--no-save",
            "--verbose",
            "--no-color",
            "--format",
            "json",
        )

        # Verify scan succeeded
        assert result.exit_code == 0

        # Verify history was NOT created
        assert not history_file.exists()

    def test_scan_subdirectory_of_tracked_project_does_not_save(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Integration test: scanning a subdirectory must not save to project history.

        Steps:
        1. create a tracked project (write `.statsvy/project.json`)
        2. run `statsvy scan` in the project root (should create history)
        3. run `statsvy scan subdir` while CWD is project root (should NOT add)
        """
        # Arrange: create project root with .statsvy and a subdirectory
        statsvy_dir = tmp_path / ".statsvy"
        statsvy_dir.mkdir()
        (tmp_path / "test_file.py").write_text("# root file")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file.py").write_text("# inner file")

        # project.json points to the project root
        (statsvy_dir / "project.json").write_text(
            json.dumps(
                {
                    "name": "p",
                    "path": str(tmp_path),
                    "date_added": "2026-02-14",
                    "last_scan": None,
                }
            )
        )

        history_file = statsvy_dir / "history.json"

        # Act: first scan (project root) — should create one history entry
        result1 = _invoke_scan(runner, tmp_path)
        assert result1.exit_code == 0
        assert history_file.exists()
        data = history_file.read_text()
        assert "metrics" in data

        # Act: scan a subdirectory while CWD is still project root
        result2 = _invoke_scan(runner, tmp_path, "subdir")
        assert result2.exit_code == 0

        # Assert: history still contains only the original entry
        parsed = json.loads(history_file.read_text())
        assert len(parsed) == 1
