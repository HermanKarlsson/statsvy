"""Test suite for the Analyzer module basic metrics.

Tests verify that Analyzer propagates ScanResult metadata into Metrics correctly.
"""

import tempfile
from datetime import datetime
from pathlib import Path

from statsvy.core.analyzer import Analyzer
from statsvy.data.metrics import Metrics
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


class TestAnalyzerBasicMetrics:
    """Tests that Analyzer propagates ScanResult metadata into Metrics correctly."""

    def _analyzer(self, tmpdir: str) -> Analyzer:
        return Analyzer("test", Path(tmpdir))

    def test_returns_metrics_instance(self) -> None:
        """Test that analyze() returns a Metrics object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._analyzer(tmpdir).analyze(_make_scan_result([]))
            assert isinstance(result, Metrics)

    def test_propagates_total_files(self) -> None:
        """Test that Metrics.total_files equals ScanResult.total_files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._analyzer(tmpdir).analyze(
                ScanResult(total_files=42, total_size_bytes=0, scanned_files=())
            )
            assert result.total_files == 42

    def test_propagates_total_size_bytes(self) -> None:
        """Test that Metrics.total_size_bytes equals ScanResult.total_size_bytes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._analyzer(tmpdir).analyze(
                ScanResult(total_files=1, total_size_bytes=1024000, scanned_files=())
            )
            assert result.total_size_bytes == 1024000

    def test_calculates_total_size_kb(self) -> None:
        """Test that total_size_kb is total_size_bytes // 1024."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._analyzer(tmpdir).analyze(
                ScanResult(total_files=1, total_size_bytes=2048, scanned_files=())
            )
            assert result.total_size_kb == 2

    def test_calculates_total_size_mb(self) -> None:
        """Test that total_size_mb is total_size_bytes // (1024 * 1024)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._analyzer(tmpdir).analyze(
                ScanResult(
                    total_files=1, total_size_bytes=2 * 1024 * 1024, scanned_files=()
                )
            )
            assert result.total_size_mb == 2

    def test_sets_name_on_metrics(self) -> None:
        """Test that Metrics.name matches the name given to Analyzer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = Analyzer("my_analysis", Path(tmpdir))
            result = analyzer.analyze(_make_scan_result([]))
            assert result.name == "my_analysis"

    def test_sets_path_on_metrics(self) -> None:
        """Test that Metrics.path matches the path given to Analyzer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            analyzer = Analyzer("proj", path)
            result = analyzer.analyze(_make_scan_result([]))
            assert result.path == path

    def test_timestamp_is_close_to_now(self) -> None:
        """Test that Metrics.timestamp is set to approximately the current time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            before = datetime.now()
            result = self._analyzer(tmpdir).analyze(_make_scan_result([]))
            after = datetime.now()
            assert before <= result.timestamp <= after
