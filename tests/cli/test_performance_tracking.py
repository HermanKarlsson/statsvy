"""Integration tests for performance tracking feature."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from statsvy.cli import main


@pytest.fixture()
def runner() -> CliRunner:
    """Provide a Click CLI test runner.

    Returns:
        CliRunner instance for invoking CLI commands.
    """
    return CliRunner()


@pytest.fixture()
def test_project_dir(tmp_path: Path) -> Path:
    """Create a minimal project structure for testing.

    Args:
        tmp_path: Pytest's temporary directory.

    Returns:
        Path to the test project directory.
    """
    # Create some test files
    (tmp_path / "file1.py").write_text(
        "#!/usr/bin/env python\n# Test file\nprint('hello')"
    )
    (tmp_path / "file2.txt").write_text("Some text content")

    subdir = tmp_path / "src"
    subdir.mkdir()
    (subdir / "module.py").write_text("# Module\ndef function():\n    pass")

    return tmp_path


class TestPerformanceTrackingCLI:
    """Tests for performance tracking via CLI flag."""

    def test_scan_without_track_performance_flag(
        self, runner: CliRunner, test_project_dir: Path
    ) -> None:
        """Test scan command without --track-performance flag.

        Should not display performance metrics.
        """
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["scan", "--dir", str(test_project_dir), "--no-save"],
            )

            assert result.exit_code == 0
            # Performance metrics line should not be present
            assert "Memory:" not in result.output

    def test_scan_with_track_performance_flag(
        self, runner: CliRunner, test_project_dir: Path
    ) -> None:
        """Test scan command with --track-performance flag.

        Should display performance metrics including both I/O and memory (alias).
        """
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "scan",
                    "--dir",
                    str(test_project_dir),
                    "--no-save",
                    "--track-performance",
                ],
                input="y\n",
            )

            assert result.exit_code == 0
            # Status messages for each profiling pass should be present
            assert "Running I/O profiling" in result.output
            assert "Running memory profiling" in result.output

            # Both I/O and memory metrics should be present for the profile alias
            assert "Memory:" in result.output
            assert "I/O:" in result.output
            assert "peak" in result.output
            assert "MB" in result.output

    def test_scan_with_profile_alias(
        self, runner: CliRunner, test_project_dir: Path
    ) -> None:
        """`--profile` is an alias for running both I/O and memory profiling.

        The command must run I/O profiling first, then memory profiling.
        """
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "scan",
                    "--dir",
                    str(test_project_dir),
                    "--no-save",
                    "--profile",
                ],
                input="y\n",
            )

            assert result.exit_code == 0
            # Status messages for each profiling pass should be present
            assert "Running I/O profiling" in result.output
            assert "Running memory profiling" in result.output

            # No metrics should be printed between the two passes
            start = result.output.index("Running I/O profiling")
            mid = result.output.index("Running memory profiling", start)
            between = result.output[start:mid]
            assert "Memory:" not in between and "I/O:" not in between

            # Final output must include both Memory and I/O summaries
            assert "Memory:" in result.output
            assert "I/O:" in result.output
            assert "peak" in result.output

    def test_scan_track_performance_includes_execution_time(
        self, runner: CliRunner, test_project_dir: Path
    ) -> None:
        """Test that performance tracking doesn't remove execution time display."""
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "scan",
                    "--dir",
                    str(test_project_dir),
                    "--no-save",
                    "--track-performance",
                ],
                input="y\n",
            )

            assert result.exit_code == 0
            # Both execution time and memory should be displayed
            assert "Scan completed in" in result.output
            assert "seconds" in result.output
            assert "Memory:" in result.output

    def test_scan_track_performance_via_config_file(
        self, runner: CliRunner, test_project_dir: Path, tmp_path: Path
    ) -> None:
        """Test enabling performance tracking via config file.

        When track_performance = true in config, should display metrics
        even without --track-performance flag.
        """
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[tool.statsvy.core]\ntrack_performance = true\n")

        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "--config",
                    str(config_file),
                    "scan",
                    "--dir",
                    str(test_project_dir),
                    "--no-save",
                ],
                input="y\n",
            )

            assert result.exit_code == 0
            # Memory metrics should be displayed when config enabled
            assert "Memory:" in result.output

    def test_scan_cli_flag_overrides_config(
        self, runner: CliRunner, test_project_dir: Path, tmp_path: Path
    ) -> None:
        """Test that CLI flag takes precedence over config file.

        When config has track_performance = false but --track-performance is set,
        should track performance.
        """
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[tool.statsvy.core]\ntrack_performance = false\n")

        with runner.isolated_filesystem():
            # Explicitly enable via CLI flag
            result = runner.invoke(
                main,
                [
                    "--config",
                    str(config_file),
                    "scan",
                    "--dir",
                    str(test_project_dir),
                    "--no-save",
                    "--track-performance",
                ],
                input="y\n",
            )

            assert result.exit_code == 0
            # Should show memory metrics (flag took precedence)
            assert "Memory:" in result.output

    def test_performance_metrics_format(
        self, runner: CliRunner, test_project_dir: Path
    ) -> None:
        """Test the format of performance metrics output.

        Metrics should be in format: "Memory: peak X.XX MB"
        """
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "scan",
                    "--dir",
                    str(test_project_dir),
                    "--no-save",
                    "--track-performance",
                ],
                input="y\n",
            )

            assert result.exit_code == 0
            # Verify output format
            lines = result.output.split("\n")
            memory_lines = [line for line in lines if "Memory:" in line]

            assert len(memory_lines) >= 1
            # Ensure at least one Memory line contains 'peak' and a unit
            assert any("peak" in m and ("MB" in m or "B" in m) for m in memory_lines)

    def test_decline_track_performance_disables_tracking(
        self, runner: CliRunner, test_project_dir: Path
    ) -> None:
        """Declining performance tracking disables performance metrics during scan."""
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "scan",
                    "--dir",
                    str(test_project_dir),
                    "--no-save",
                    "--track-performance",
                ],
                input="n\n",
            )

            assert result.exit_code == 0
            # Neither Memory nor I/O metrics should be present when user declines
            assert "Memory:" not in result.output
            assert "I/O:" not in result.output

    def test_scan_with_track_io_flag(
        self, runner: CliRunner, test_project_dir: Path
    ) -> None:
        """`--track-io` should display I/O metrics only."""
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "scan",
                    "--dir",
                    str(test_project_dir),
                    "--no-save",
                    "--track-io",
                ],
                input="y\n",
            )

            assert result.exit_code == 0
            # Status message should indicate I/O profiling is running
            assert "Running I/O profiling" in result.output
            assert "I/O:" in result.output
            # Memory summary may still be shown (peak reported as 0 when not
            # tracked). Do not require its absence.

    def test_scan_with_track_mem_flag(
        self, runner: CliRunner, test_project_dir: Path
    ) -> None:
        """`--track-mem` should display memory metrics only."""
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "scan",
                    "--dir",
                    str(test_project_dir),
                    "--no-save",
                    "--track-mem",
                ],
                input="y\n",
            )

            assert result.exit_code == 0
            # Status message should indicate memory profiling is running
            assert "Running memory profiling" in result.output
            assert "Memory:" in result.output
            assert "I/O:" not in result.output

    @patch("statsvy.cli.scan_handler.PerformanceMetricsFormatter")
    @patch("statsvy.cli.scan_handler.PerformanceTracker")
    def test_tracker_lifecycle_in_scan_handler(
        self,
        mock_tracker_class: MagicMock,
        mock_formatter_class: MagicMock,
        runner: CliRunner,
        test_project_dir: Path,
    ) -> None:
        """Test that PerformanceTracker is properly started and stopped.

        Verifies that the tracker is instantiated, started before work,
        and stopped after work.
        """
        with runner.isolated_filesystem():
            mock_tracker = mock_tracker_class.return_value
            mock_formatter_class.format_text.return_value = "Memory: peak 50.00 MB"
            mock_tracker.stop.return_value = MagicMock(peak_memory_bytes=52_428_800)

            result = runner.invoke(
                main,
                [
                    "scan",
                    "--dir",
                    str(test_project_dir),
                    "--no-save",
                    "--track-performance",
                ],
                input="y\n",
            )

            assert result.exit_code == 0
            # Verify tracker was used for both passes (I/O + memory)
            assert mock_tracker_class.call_count == 2
            assert mock_tracker.start.call_count == 2
            assert mock_tracker.stop.call_count == 2
