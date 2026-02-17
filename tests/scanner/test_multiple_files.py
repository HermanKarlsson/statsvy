"""Test suite for the Scanner module - multiple files.

Tests for directories containing multiple files.
"""

import tempfile
from pathlib import Path

from statsvy.core.scanner import Scanner


class TestMultipleFiles:
    """Tests for directories containing multiple files."""

    def test_multiple_files_counted(self) -> None:
        """Test that all files are counted when there are multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ("a.py", "b.py", "c.txt"):
                (Path(tmpdir) / name).write_text("x")
            result = Scanner(tmpdir).scan()
            assert result.total_files == 3

    def test_multiple_files_size_accumulated(self) -> None:
        """Test that total_size_bytes is the sum of all individual file sizes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contents = {"a.txt": "Hello", "b.txt": "World", "c.txt": "Test"}
            for name, content in contents.items():
                (Path(tmpdir) / name).write_text(content)
            expected = sum(len(c.encode()) for c in contents.values())
            result = Scanner(tmpdir).scan()
            assert result.total_size_bytes == expected

    def test_all_files_present_in_scanned_files(self) -> None:
        """Test that every file appears in scanned_files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = [Path(tmpdir) / n for n in ("a.py", "b.py", "c.txt")]
            for f in files:
                f.write_text("x")
            result = Scanner(tmpdir).scan()
            for f in files:
                assert f in result.scanned_files
