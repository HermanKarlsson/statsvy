"""Test suite for the Scanner module - gitignore parsing.

Tests for automatic .gitignore parsing.
"""

import tempfile
from pathlib import Path

from statsvy.core.scanner import Scanner


class TestGitignoreParsing:
    """Tests for automatic .gitignore parsing."""

    def test_gitignore_patterns_are_applied(self) -> None:
        """Test that patterns from .gitignore are respected during scan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / ".gitignore").write_text("*.log\n")
            (Path(tmpdir) / "keep.txt").write_text("keep")
            (Path(tmpdir) / "skip.log").write_text("skip")
            result = Scanner(tmpdir, no_gitignore=False).scan()
            names = {f.name for f in result.scanned_files}
            assert "skip.log" not in names
            assert "keep.txt" in names

    def test_gitignore_comments_are_ignored(self) -> None:
        """Test comment lines starting with # in .gitignore are not patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / ".gitignore").write_text(
                "# This is a comment\n*.log\n# Another\n*.tmp\n"
            )
            scanner = Scanner(tmpdir, no_gitignore=False)
            assert "*.log" in scanner.ignore
            assert "*.tmp" in scanner.ignore
            assert not any(p.startswith("#") for p in scanner.ignore)

    def test_gitignore_empty_lines_are_ignored(self) -> None:
        """Test that blank lines in .gitignore are not added as patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / ".gitignore").write_text("*.log\n\n\n*.tmp\n")
            scanner = Scanner(tmpdir, no_gitignore=False)
            assert "" not in scanner.ignore

    def test_gitignore_directory_patterns_exclude_contents(self) -> None:
        """Test that directory patterns from .gitignore exclude all contained files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / ".gitignore").write_text("build\nnode_modules\n")
            (Path(tmpdir) / "main.py").write_text("main")
            (Path(tmpdir) / "build").mkdir()
            (Path(tmpdir) / "build" / "out.o").write_text("out")
            (Path(tmpdir) / "node_modules").mkdir()
            (Path(tmpdir) / "node_modules" / "pkg.js").write_text("pkg")
            result = Scanner(tmpdir, no_gitignore=False).scan()
            names = {f.name for f in result.scanned_files}
            assert "out.o" not in names
            assert "pkg.js" not in names
            assert "main.py" in names

    def test_no_gitignore_true_ignores_gitignore_file(self) -> None:
        """Test that no_gitignore=True causes .gitignore patterns to be disregarded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / ".gitignore").write_text("*.log\n")
            (Path(tmpdir) / "keep.txt").write_text("keep")
            (Path(tmpdir) / "keep.log").write_text("log")
            result = Scanner(tmpdir, no_gitignore=True).scan()
            assert result.total_files == 3

    def test_missing_gitignore_does_not_cause_error(self) -> None:
        """Test that a missing .gitignore file is handled without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file.txt").write_text("content")
            result = Scanner(tmpdir, no_gitignore=False).scan()
            assert result.total_files == 1

    def test_gitignore_patterns_combined_with_explicit_ignore(self) -> None:
        """Test that .gitignore patterns are merged with given ignore patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / ".gitignore").write_text("*.log\n")
            (Path(tmpdir) / "keep.txt").write_text("keep")
            (Path(tmpdir) / "skip.log").write_text("log")
            (Path(tmpdir) / "skip.tmp").write_text("tmp")
            result = Scanner(tmpdir, ignore=("*.tmp",), no_gitignore=False).scan()
            names = {f.name for f in result.scanned_files}
            assert "skip.log" not in names
            assert "skip.tmp" not in names
            assert "keep.txt" in names

    def test_gitignore_trailing_slash_stripped(self) -> None:
        """Test that trailing slashes on .gitignore patterns are stripped correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / ".gitignore").write_text("build/\n")
            scanner = Scanner(tmpdir, no_gitignore=False)
            assert "build" in scanner.ignore
            assert "build/" not in scanner.ignore
