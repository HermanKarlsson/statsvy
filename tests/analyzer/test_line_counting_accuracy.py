"""Test suite for the Analyzer module line counting accuracy.

Tests verify accurate total_lines counting across files.
"""

import tempfile
from pathlib import Path

from statsvy.core.analyzer import Analyzer
from statsvy.data.scan_result import ScanResult


def _make_scan_result(files: list[Path], size: int = 0) -> ScanResult:
    """Build a ScanResult from a list of file paths.

    Args:
        files: List of Path objects to include.
        size: Total size in bytes to report.

    Returns:
        A ScanResult populated with the given files.
    """
    return ScanResult(
        total_files=len(files),
        total_size_bytes=size,
        scanned_files=tuple(files),
    )


class TestLineCountingAccuracy:
    """Tests for accurate total_lines counting across files."""

    def test_counts_lines_in_single_file(self) -> None:
        """Test that a three-line file produces total_lines == 3."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "test.py"
            f.write_text("line1\nline2\nline3\n")
            result = Analyzer("t", Path(tmpdir)).analyze(_make_scan_result([f]))
            assert result.total_lines == 3

    def test_empty_file_contributes_zero_lines(self) -> None:
        """Test that an empty file adds 0 to total_lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "empty.py"
            f.write_text("")
            result = Analyzer("t", Path(tmpdir)).analyze(_make_scan_result([f]))
            assert result.total_lines == 0

    def test_lines_accumulated_across_multiple_files(self) -> None:
        """Test that total_lines sums lines from all provided files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = Path(tmpdir) / "a.py"
            f1.write_text("line1\nline2\n")
            f2 = Path(tmpdir) / "b.py"
            f2.write_text("line1\nline2\nline3\n")
            result = Analyzer("t", Path(tmpdir)).analyze(_make_scan_result([f1, f2]))
            assert result.total_lines == 5

    def test_whitespace_only_lines_are_counted(self) -> None:
        """Test that lines containing only whitespace are included in total_lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "test.py"
            f.write_text("line1\n   \nline3\n")
            result = Analyzer("t", Path(tmpdir)).analyze(_make_scan_result([f]))
            assert result.total_lines == 3

    def test_file_without_trailing_newline(self) -> None:
        """Test that a file lacking a trailing newline still reports one line."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "test.py"
            f.write_text("only one line")
            result = Analyzer("t", Path(tmpdir)).analyze(_make_scan_result([f]))
            assert result.total_lines == 1

    def test_no_files_produces_zero_total_lines(self) -> None:
        """Test that an empty file list results in total_lines == 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = Analyzer("t", Path(tmpdir)).analyze(_make_scan_result([]))
            assert result.total_lines == 0
