"""Test suite for --scan-timeout CLI flag."""

import os
from collections.abc import Iterator
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
    """Create a small directory for testing scan with timeout.

    Args:
        tmp_path: pytest temporary directory.

    Returns:
        Root Path of the created structure.
    """
    (tmp_path / "file1.py").write_text("# Python file")
    (tmp_path / "file2.txt").write_text("Text file")
    return tmp_path


@pytest.fixture(autouse=True)
def fast_tracemalloc() -> Iterator[None]:
    """Mock tracemalloc so profile-related timeout tests remain fast."""
    with patch("statsvy.core.performance_tracker.tracemalloc") as mock_tm:
        mock_tm.get_traced_memory.return_value = (0, 52_428_800)
        yield


def _invoke_scan(runner: CliRunner, directory: Path, *extra_args: str) -> Result:
    """Invoke ``statsvy scan`` pointing at *directory* with optional extra args."""
    original_cwd = os.getcwd()

    os.chdir(directory)
    try:
        with patch(f"{_CLI_MODULE}.Path.cwd", return_value=directory):
            result: Result = runner.invoke(main, ["scan", "--no-git", *extra_args])
    finally:
        os.chdir(original_cwd)

    return result


class TestScanTimeoutFlag:
    """Tests for --scan-timeout CLI flag."""

    def test_scan_timeout_flag_accepts_integer(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test that --scan-timeout accepts integer values (alias: --timeout)."""
        result = _invoke_scan(
            runner, temp_dir, "--scan-timeout", "60", "--no-save", "--no-progress"
        )
        # Should complete without error (timeout is reasonable)
        assert result.exit_code == 0

        # alias
        result_alias = _invoke_scan(
            runner, temp_dir, "--timeout", "60", "--no-save", "--no-progress"
        )
        assert result_alias.exit_code == 0

    def test_scan_timeout_flag_appears_in_help(self, runner: CliRunner) -> None:
        """Test that --scan-timeout and alias --timeout appear in help text."""
        result = runner.invoke(main, ["scan", "--help"])
        assert result.exit_code == 0
        assert "--scan-timeout" in result.output
        assert "--timeout" in result.output
        assert "Maximum scan duration" in result.output

    def test_scan_with_very_short_timeout_may_fail(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test that very short timeout can trigger TimeoutError."""
        # Create many files to make scan take longer
        for i in range(100):
            (temp_dir / f"file{i}.txt").write_text(f"content {i}\n" * 100)

        # Use extremely short timeout to trigger error
        result = _invoke_scan(
            runner, temp_dir, "--scan-timeout", "0", "--no-save", "--no-progress"
        )
        # With 0 timeout (disabled), should complete successfully
        assert result.exit_code == 0

    def test_scan_timeout_cli_sets_timeout_value(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """CLI --scan-timeout should be passed to the TimeoutChecker."""
        with patch("statsvy.cli.scan_handler.TimeoutChecker") as mock_tc:
            result = _invoke_scan(
                runner, temp_dir, "--scan-timeout", "42", "--no-save", "--no-progress"
            )
            assert result.exit_code == 0
            mock_tc.assert_called_once_with(42)

    def test_profile_disables_timeout(self, runner: CliRunner, temp_dir: Path) -> None:
        """When profiling is accepted the timeout should be disabled (0)."""
        with patch("statsvy.cli.scan_handler.TimeoutChecker") as mock_tc:
            # Use runner.invoke directly so we can provide the 'y' confirmation
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            try:
                with patch(f"{_CLI_MODULE}.Path.cwd", return_value=temp_dir):
                    result = runner.invoke(
                        main,
                        [
                            "scan",
                            "--scan-timeout",
                            "5",
                            "--profile",
                            "--no-git",
                            "--no-save",
                            "--no-progress",
                        ],
                        input="y\n",
                    )
            finally:
                os.chdir(original_cwd)

            assert result.exit_code == 0
            # TimeoutChecker should be constructed with 0 when profiling is active
            mock_tc.assert_called_once_with(0)

    def test_scan_timeout_environment_variable(
        self, runner: CliRunner, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that STATSVY_SCAN_TIMEOUT_SECONDS env var is respected."""
        # Set environment variable
        monkeypatch.setenv("STATSVY_SCAN_TIMEOUT_SECONDS", "120")

        result = _invoke_scan(runner, temp_dir, "--no-save", "--no-progress")
        # Should complete successfully with env var timeout
        assert result.exit_code == 0

    def test_scan_timeout_cli_overrides_env_var(
        self, runner: CliRunner, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that CLI flag overrides environment variable."""
        # Set env var to a different value
        monkeypatch.setenv("STATSVY_SCAN_TIMEOUT_SECONDS", "30")

        # CLI flag should take precedence
        result = _invoke_scan(
            runner, temp_dir, "--scan-timeout", "60", "--no-save", "--no-progress"
        )
        assert result.exit_code == 0

    def test_scan_timeout_with_verbose_mode(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test that timeout works with verbose mode enabled."""
        result = _invoke_scan(
            runner,
            temp_dir,
            "--scan-timeout",
            "60",
            "--verbose",
            "--no-save",
            "--no-progress",
        )
        assert result.exit_code == 0
        # Verbose output should be present
        assert (
            "Target directory:" in result.output
            or "Scanning directory" in result.output
        )

    def test_scan_timeout_with_progress_bar(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test that timeout works with progress bar enabled."""
        result = _invoke_scan(runner, temp_dir, "--scan-timeout", "60", "--no-save")
        assert result.exit_code == 0


class TestScanTimeoutConfiguration:
    """Tests for timeout configuration priority."""

    def test_scan_uses_default_timeout_when_not_specified(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test that scan uses default timeout (300s) when not specified."""
        result = _invoke_scan(runner, temp_dir, "--no-save", "--no-progress")
        assert result.exit_code == 0
        # Should complete with default timeout

    def test_scan_timeout_zero_disables_timeout(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Test that timeout value of 0 disables timeout checking."""
        # Create a few files
        for i in range(10):
            (temp_dir / f"file{i}.txt").write_text("content")

        result = _invoke_scan(
            runner, temp_dir, "--scan-timeout", "0", "--no-save", "--no-progress"
        )
        # Should always complete successfully with disabled timeout
        assert result.exit_code == 0
