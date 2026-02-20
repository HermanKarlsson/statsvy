"""Test suite for the Scanner module - return types.

Tests for the type and structure of ScanResult.
"""

import tempfile
from pathlib import Path

from statsvy.core.scanner import Scanner
from statsvy.data.scan_result import ScanResult


class TestScanReturnType:
    """Tests for the type and structure of ScanResult."""

    def test_scan_returns_scan_result_instance(self) -> None:
        """Test that scan() returns a ScanResult object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = Scanner(tmpdir).scan()
            assert isinstance(result, ScanResult)

    def test_scan_result_has_total_files_attribute(self) -> None:
        """Test that ScanResult exposes total_files as an integer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "a.txt").write_text("x")
            result = Scanner(tmpdir).scan()
            assert isinstance(result.total_files, int)

    def test_scan_result_has_total_size_bytes_attribute(self) -> None:
        """Test that ScanResult exposes total_size_bytes as an integer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "a.txt").write_text("x")
            result = Scanner(tmpdir).scan()
            assert isinstance(result.total_size_bytes, int)

    def test_scan_result_has_scanned_files_as_list(self) -> None:
        """Test that ScanResult.scanned_files is a tuple."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = Scanner(tmpdir).scan()
            assert isinstance(result.scanned_files, tuple)

    def test_scan_result_scanned_files_contain_path_objects(self) -> None:
        """Test that all entries in scanned_files are Path objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "a.txt").write_text("x")
            result = Scanner(tmpdir).scan()
            assert all(isinstance(f, Path) for f in result.scanned_files)

    def test_scan_result_includes_bytes_read(self) -> None:
        """ScanResult should include a bytes_read integer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "a.txt"
            p.write_text("hello")
            result = Scanner(tmpdir).scan()
            assert isinstance(result.bytes_read, int)
            # bytes_read should be >= total_size_bytes for the files actually read
            assert result.bytes_read >= result.total_size_bytes
