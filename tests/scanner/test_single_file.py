"""Test suite for the Scanner module - single file.

Tests for directories containing exactly one file.
"""

import tempfile
from pathlib import Path

from statsvy.core.scanner import Scanner


class TestSingleFile:
    """Tests for directories containing exactly one file."""

    def test_single_file_counted(self) -> None:
        """Test that a single file increments total_files to 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file.txt").write_text("Hello")
            result = Scanner(tmpdir).scan()
            assert result.total_files == 1

    def test_single_file_size_matches(self) -> None:
        """Test that total_size_bytes equals the byte length of the file content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = "Hello, World!"
            (Path(tmpdir) / "file.txt").write_text(content)
            result = Scanner(tmpdir).scan()
            assert result.total_size_bytes == len(content.encode())

    def test_single_file_appears_in_scanned_files(self) -> None:
        """Test that the scanned file path is present in scanned_files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "file.txt"
            file_path.write_text("content")
            result = Scanner(tmpdir).scan()
            assert file_path in result.scanned_files

    def test_empty_file_is_counted(self) -> None:
        """Test that a zero-byte file is still counted as a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "empty.txt").write_text("")
            result = Scanner(tmpdir).scan()
            assert result.total_files == 1
            assert result.total_size_bytes == 0

    def test_binary_file_is_counted(self) -> None:
        """Test that binary files are counted and their size is recorded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            binary_data = b"\x00\x01\x02\x03\x04"
            (Path(tmpdir) / "binary.bin").write_bytes(binary_data)
            result = Scanner(tmpdir).scan()
            assert result.total_files == 1
            assert result.total_size_bytes == len(binary_data)
