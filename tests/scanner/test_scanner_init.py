"""Test suite for the Scanner module - initialization.

Tests for Scanner initialization and validation.
"""

import tempfile
from pathlib import Path

import pytest

from statsvy.core.scanner import Scanner


class TestScannerInit:
    """Tests for Scanner initialization and validation."""

    def test_scanner_accepts_string_path(self) -> None:
        """Test that Scanner accepts and converts string paths to Path objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = Scanner(tmpdir)
            assert isinstance(scanner.root_path, Path)
            assert str(scanner.root_path) == tmpdir

    def test_scanner_accepts_pathlib_path(self) -> None:
        """Test that Scanner accepts pathlib.Path objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            scanner = Scanner(path)
            assert scanner.root_path == path

    def test_scanner_raises_value_error_for_nonexistent_path(self) -> None:
        """Test that Scanner raises ValueError for a path that does not exist."""
        with pytest.raises(ValueError, match="does not exist"):
            Scanner("/nonexistent/path/that/should/not/exist")

    def test_scanner_raises_value_error_when_path_is_file(self) -> None:
        """Test Scanner raises ValueError when given a file instead of a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_file.txt"
            file_path.write_text("content")
            with pytest.raises(ValueError, match="is not a directory"):
                Scanner(str(file_path))

    def test_scanner_default_ignore_is_empty_tuple(self) -> None:
        """Test that ignore defaults to empty tuple when no gitignore exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = Scanner(tmpdir, no_gitignore=True)
            assert scanner.ignore == ()

    def test_scanner_stores_provided_ignore_patterns(self) -> None:
        """Test that Scanner stores provided ignore patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            patterns = ("*.log", "*.tmp")
            scanner = Scanner(tmpdir, ignore=patterns, no_gitignore=True)
            assert scanner.ignore == patterns

    def test_scanner_no_gitignore_defaults_to_false(self) -> None:
        """Test that no_gitignore parameter defaults to False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = Scanner(tmpdir)
            assert scanner.no_gitignore is False

    def test_scanner_stores_no_gitignore_true(self) -> None:
        """Test that Scanner stores no_gitignore=True correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = Scanner(tmpdir, no_gitignore=True)
            assert scanner.no_gitignore is True
