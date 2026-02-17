"""Test suite for the Scanner module - consistency.

Tests for idempotency and side-effect-free scanning.
"""

import tempfile
from pathlib import Path

from statsvy.core.scanner import Scanner


class TestScanConsistency:
    """Tests for idempotency and side-effect-free scanning."""

    def test_repeated_scan_returns_same_file_count(self) -> None:
        """Test that scanning the same directory twice yields the same total_files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file.txt").write_text("content")
            scanner = Scanner(tmpdir)
            assert scanner.scan().total_files == scanner.scan().total_files

    def test_repeated_scan_returns_same_total_size(self) -> None:
        """Test scanning the same directory twice yields the same total_size_bytes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file.txt").write_text("content")
            scanner = Scanner(tmpdir)
            assert scanner.scan().total_size_bytes == scanner.scan().total_size_bytes

    def test_repeated_scan_returns_same_scanned_files(self) -> None:
        """Test that scanned_files is identical across repeated scans."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file.txt").write_text("content")
            scanner = Scanner(tmpdir)
            r1, r2 = scanner.scan(), scanner.scan()
            assert sorted(r1.scanned_files) == sorted(r2.scanned_files)

    def test_scan_does_not_create_new_files(self) -> None:
        """Test that scanning does not modify the directory contents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file.txt").write_text("content")
            before = set(Path(tmpdir).rglob("*"))
            Scanner(tmpdir).scan()
            after = set(Path(tmpdir).rglob("*"))
            assert before == after
