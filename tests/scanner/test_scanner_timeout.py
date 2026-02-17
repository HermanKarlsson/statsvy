"""Test suite for Scanner timeout functionality."""

import tempfile
from dataclasses import replace
from pathlib import Path
from time import sleep
from unittest.mock import patch

import pytest

from statsvy.core.scanner import Scanner
from statsvy.data.config import Config
from statsvy.utils.timeout_checker import TimeoutChecker


class TestScannerTimeout:
    """Tests for Scanner timeout behavior."""

    def test_scanner_completes_within_timeout(self) -> None:
        """Scanner should complete successfully when within timeout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a few simple files
            for i in range(5):
                (Path(tmpdir) / f"file{i}.txt").write_text("test content")

            scanner = Scanner(tmpdir)
            timeout_checker = TimeoutChecker(10)  # 10 second timeout
            timeout_checker.start()

            result = scanner.scan(timeout_checker)
            assert result.total_files == 5

    def test_scanner_without_timeout_checker_works(self) -> None:
        """Scanner should work normally when no timeout_checker provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file.txt").write_text("test")

            scanner = Scanner(tmpdir)
            result = scanner.scan()  # No timeout checker
            assert result.total_files == 1

    def test_scanner_respects_timeout_in_progress_mode(self) -> None:
        """Scanner with progress bar should respect timeout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files
            for i in range(10):
                (Path(tmpdir) / f"file{i}.txt").write_text("content")

            scanner = Scanner(tmpdir)
            timeout_checker = TimeoutChecker(0.001)  # 1ms timeout
            timeout_checker.start()

            # Mock the _process_path to be slow
            original_process = scanner._process_path

            def slow_process(
                path: Path, scan_data: dict[str, int | list[Path]]
            ) -> None:
                sleep(0.01)  # 10ms per file
                return original_process(path, scan_data)

            with (
                patch.object(scanner, "_process_path", side_effect=slow_process),
                pytest.raises(TimeoutError, match=r"exceeded 0\.001s timeout limit"),
            ):
                # Should timeout before processing all files
                scanner.scan(timeout_checker)

    def test_scanner_timeout_message_includes_context(self) -> None:
        """TimeoutError from scanner should include 'file discovery' context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create many files to ensure timeout
            for i in range(100):
                (Path(tmpdir) / f"file{i}.txt").write_text("content")

            scanner = Scanner(tmpdir)
            timeout_checker = TimeoutChecker(0.001)
            timeout_checker.start()

            # Mock rglob to return files slowly
            original_process = scanner._process_path

            def slow_process(
                path: Path, scan_data: dict[str, int | list[Path]]
            ) -> None:
                sleep(0.01)
                return original_process(path, scan_data)

            with (
                patch.object(scanner, "_process_path", side_effect=slow_process),
                pytest.raises(TimeoutError, match="file discovery"),
            ):
                scanner.scan(timeout_checker)

    def test_scanner_with_disabled_timeout(self) -> None:
        """Scanner should not timeout when timeout_seconds is 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(5):
                (Path(tmpdir) / f"file{i}.txt").write_text("content")

            scanner = Scanner(tmpdir)
            timeout_checker = TimeoutChecker(0)  # Disabled timeout
            timeout_checker.start()

            result = scanner.scan(timeout_checker)
            assert result.total_files == 5


class TestScannerTimeoutWithoutProgress:
    """Tests for Scanner timeout behavior without progress bar."""

    def test_scanner_respects_timeout_without_progress(self) -> None:
        """Scanner without progress bar should respect timeout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files
            for i in range(10):
                (Path(tmpdir) / f"file{i}.txt").write_text("content")

            config = Config.default()
            # Create a config with progress disabled using dataclasses.replace
            core_config = replace(config.core, show_progress=False)
            config_no_progress = replace(config, core=core_config)

            scanner = Scanner(tmpdir, config=config_no_progress)
            timeout_checker = TimeoutChecker(0.001)
            timeout_checker.start()

            # Mock the _process_path to be slow
            original_process = scanner._process_path

            def slow_process(
                path: Path, scan_data: dict[str, int | list[Path]]
            ) -> None:
                sleep(0.01)
                return original_process(path, scan_data)

            with (
                patch.object(scanner, "_process_path", side_effect=slow_process),
                pytest.raises(TimeoutError, match=r"exceeded 0\.001s timeout limit"),
            ):
                scanner.scan(timeout_checker)
