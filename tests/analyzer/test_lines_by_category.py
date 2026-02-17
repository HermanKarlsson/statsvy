"""Test suite for the Analyzer module lines by category.

Tests verify lines_by_category grouping in Metrics.
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


class TestLinesByCategory:
    """Tests for lines_by_category grouping in Metrics."""

    def test_metrics_exposes_lines_by_category(self) -> None:
        """Test that Metrics has a lines_by_category mapping."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = Analyzer("t", Path(tmpdir)).analyze(_make_scan_result([]))
            assert hasattr(result, "lines_by_category")

            assert isinstance(result.lines_by_category, Mapping)

    def test_lines_by_category_not_empty_when_files_processed(self) -> None:
        """Test that lines_by_category contains entries when files are analyzed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "script.py"
            f.write_text("code\n")
            result = Analyzer("t", Path(tmpdir)).analyze(_make_scan_result([f]))
            assert len(result.lines_by_category) > 0
