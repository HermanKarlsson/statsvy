"""Test suite for the Analyzer module comment and blank lines.

Tests verify comment_lines and blank_lines fields on Metrics.
"""

import tempfile
from collections.abc import Mapping
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


class TestCommentAndBlankLines:
    """Tests for comment_lines and blank_lines fields on Metrics."""

    def test_metrics_exposes_comment_lines(self) -> None:
        """Test that Metrics has a comment_lines attribute."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = Analyzer("t", Path(tmpdir)).analyze(_make_scan_result([]))
            assert hasattr(result, "comment_lines")

    def test_metrics_exposes_blank_lines(self) -> None:
        """Test that Metrics has a blank_lines attribute."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = Analyzer("t", Path(tmpdir)).analyze(_make_scan_result([]))
            assert hasattr(result, "blank_lines")

    def test_metrics_exposes_comment_lines_by_lang(self) -> None:
        """Test that Metrics has a comment_lines_by_lang mapping."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = Analyzer("t", Path(tmpdir)).analyze(_make_scan_result([]))
            assert hasattr(result, "comment_lines_by_lang")

            assert isinstance(result.comment_lines_by_lang, Mapping)

    def test_metrics_exposes_blank_lines_by_lang(self) -> None:
        """Test that Metrics has a blank_lines_by_lang mapping."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = Analyzer("t", Path(tmpdir)).analyze(_make_scan_result([]))
            assert hasattr(result, "blank_lines_by_lang")

            assert isinstance(result.blank_lines_by_lang, Mapping)

    def test_blank_lines_are_non_negative(self) -> None:
        """Test that blank_lines is always >= 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "file.py"
            f.write_text("code\n\n\nmore_code\n")
            result = Analyzer("t", Path(tmpdir)).analyze(_make_scan_result([f]))
            assert result.blank_lines >= 0

    def test_comment_lines_are_non_negative(self) -> None:
        """Test that comment_lines is always >= 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "file.py"
            f.write_text("# comment\ncode\n")
            result = Analyzer("t", Path(tmpdir)).analyze(_make_scan_result([f]))
            assert result.comment_lines >= 0

    def test_no_files_yields_zero_comment_and_blank_lines(self) -> None:
        """Test that analyzing no files gives zero comment and blank lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = Analyzer("t", Path(tmpdir)).analyze(_make_scan_result([]))
            assert result.comment_lines == 0
            assert result.blank_lines == 0
