"""Test suite for the Scanner module - nested directories.

Tests for directories with nested subdirectory structures.
"""

import tempfile
from pathlib import Path

from statsvy.core.scanner import Scanner


class TestNestedDirectories:
    """Tests for directories with nested subdirectory structures."""

    def test_files_in_single_subdirectory_counted(self) -> None:
        """Test that files in one level of subdirectory are included."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "sub"
            subdir.mkdir()
            (Path(tmpdir) / "root.txt").write_text("root")
            (subdir / "nested.txt").write_text("nested")
            result = Scanner(tmpdir).scan()
            assert result.total_files == 2

    def test_files_in_deeply_nested_directories_counted(self) -> None:
        """Test that files nested multiple levels deep are included."""
        with tempfile.TemporaryDirectory() as tmpdir:
            deep = Path(tmpdir) / "a" / "b" / "c"
            deep.mkdir(parents=True)
            expected_files = [
                Path(tmpdir) / "a" / "f1.txt",
                Path(tmpdir) / "a" / "b" / "f2.txt",
                deep / "f3.txt",
            ]
            for f in expected_files:
                f.write_text("x")
            result = Scanner(tmpdir).scan()
            assert result.total_files == 3
            for f in expected_files:
                assert f in result.scanned_files

    def test_empty_subdirectories_do_not_add_to_file_count(self) -> None:
        """Test that empty subdirectories contribute zero files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "empty1").mkdir()
            (Path(tmpdir) / "empty2").mkdir()
            (Path(tmpdir) / "real.txt").write_text("content")
            result = Scanner(tmpdir).scan()
            assert result.total_files == 1
