"""Test suite for the Analyzer module sequential use.

Tests confirm Analyzer can be used multiple times without state leakage.
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


class TestAnalyzerSequentialUse:
    """Tests confirming Analyzer can be used multiple times without state leakage."""

    def test_second_analysis_does_not_affect_first_result(self) -> None:
        """Test that calling analyze() twice yields two independent Metrics objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = Analyzer("t", Path(tmpdir))
            r1 = analyzer.analyze(
                ScanResult(total_files=5, total_size_bytes=100, scanned_files=())
            )
            r2 = analyzer.analyze(
                ScanResult(total_files=10, total_size_bytes=200, scanned_files=())
            )
            assert r1.total_files == 5
            assert r2.total_files == 10

    def test_lines_do_not_accumulate_across_calls(self) -> None:
        """Test that each analyze() call starts with a fresh line count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "a.py"
            f.write_text("line1\nline2\n")
            analyzer = Analyzer("t", Path(tmpdir))
            sr = _make_scan_result([f])
            r1 = analyzer.analyze(sr)
            r2 = analyzer.analyze(sr)
            assert r1.total_lines == r2.total_lines == 2
