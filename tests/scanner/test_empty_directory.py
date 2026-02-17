"""Test suite for the Scanner module - empty directory.

Tests for scanning empty directories.
"""

import tempfile

from statsvy.core.scanner import Scanner


class TestEmptyDirectory:
    """Tests for scanning empty directories."""

    def test_empty_directory_has_zero_files(self) -> None:
        """Test that an empty directory yields total_files == 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = Scanner(tmpdir).scan()
            assert result.total_files == 0

    def test_empty_directory_has_zero_size(self) -> None:
        """Test that an empty directory yields total_size_bytes == 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = Scanner(tmpdir).scan()
            assert result.total_size_bytes == 0

    def test_empty_directory_has_empty_scanned_files(self) -> None:
        """Test that scanning an empty directory yields an empty scanned_files tuple."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = Scanner(tmpdir).scan()
            assert result.scanned_files == ()
