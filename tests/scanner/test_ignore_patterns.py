"""Test suite for the Scanner module - ignore patterns.

Tests for the ignore pattern mechanism.
"""

import tempfile
from pathlib import Path

from statsvy.core.scanner import Scanner


class TestIgnorePatterns:
    """Tests for the ignore pattern mechanism."""

    def test_ignore_by_file_extension(self) -> None:
        """Test that files matching a glob extension pattern are excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "keep.txt").write_text("keep")
            (Path(tmpdir) / "skip.log").write_text("skip")
            result = Scanner(tmpdir, ignore=("*.log",), no_gitignore=True).scan()
            assert result.total_files == 1
            assert result.scanned_files[0].name == "keep.txt"

    def test_ignore_multiple_extension_patterns(self) -> None:
        """Test that multiple ignore patterns are all applied."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "keep.py").write_text("keep")
            (Path(tmpdir) / "skip.log").write_text("skip")
            (Path(tmpdir) / "skip.tmp").write_text("skip")
            result = Scanner(
                tmpdir, ignore=("*.log", "*.tmp"), no_gitignore=True
            ).scan()
            assert result.total_files == 1
            assert result.scanned_files[0].suffix == ".py"

    def test_ignore_directory_by_name(self) -> None:
        """Test that all files inside an ignored directory are excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "main.py").write_text("main")
            build = Path(tmpdir) / "build"
            build.mkdir()
            (build / "artifact.o").write_text("artifact")
            result = Scanner(tmpdir, ignore=("build",), no_gitignore=True).scan()
            assert result.total_files == 1
            assert result.scanned_files[0].name == "main.py"

    def test_ignore_nested_directory_recursively(self) -> None:
        """Test that ignoring a directory excludes all files nested within it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "root.txt").write_text("root")
            nm = Path(tmpdir) / "node_modules"
            (nm / "sub").mkdir(parents=True)
            (nm / "pkg.js").write_text("package")
            (nm / "sub" / "index.js").write_text("index")
            result = Scanner(tmpdir, ignore=("node_modules",), no_gitignore=True).scan()
            assert result.total_files == 1
            assert result.scanned_files[0].name == "root.txt"

    def test_ignore_wildcard_directory_prefix(self) -> None:
        """Test that wildcard patterns match directory names by prefix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "main.py").write_text("main")
            test_dir = Path(tmpdir) / "test_utils"
            test_dir.mkdir()
            (test_dir / "helper.py").write_text("helper")
            result = Scanner(tmpdir, ignore=("test_*",), no_gitignore=True).scan()
            assert result.total_files == 1
            assert result.scanned_files[0].name == "main.py"

    def test_ignore_excludes_files_in_ignored_directories_deep(self) -> None:
        """Test that files deeply nested inside an ignored directory are excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file.txt").write_text("root")
            cache = Path(tmpdir) / "__pycache__"
            (cache / "sub").mkdir(parents=True)
            (cache / "cache.pyc").write_text("cache")
            (cache / "sub" / "nested.pyc").write_text("nested")
            result = Scanner(tmpdir, ignore=("__pycache__",), no_gitignore=True).scan()
            assert result.total_files == 1
            assert result.scanned_files[0].name == "file.txt"

    def test_ignore_pattern_does_not_appear_in_scanned_files(self) -> None:
        """Test that ignored files are absent from scanned_files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "keep.txt").write_text("keep")
            (Path(tmpdir) / "skip.log").write_text("ignore")
            result = Scanner(tmpdir, ignore=("*.log",), no_gitignore=True).scan()
            assert all(f.suffix != ".log" for f in result.scanned_files)

    def test_ignore_excluded_from_size_calculation(self) -> None:
        """Test that ignored files do not contribute to total_size_bytes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file.txt").write_text("hello")
            (Path(tmpdir) / "big.log").write_text("ignored_content")
            result = Scanner(tmpdir, ignore=("*.log",), no_gitignore=True).scan()
            assert result.total_size_bytes == len("hello")

    def test_empty_ignore_tuple_scans_all_files(self) -> None:
        """Test that an empty ignore tuple does not exclude any files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "a.txt").write_text("a")
            (Path(tmpdir) / "b.log").write_text("b")
            result = Scanner(tmpdir, ignore=(), no_gitignore=True).scan()
            assert result.total_files == 2

    def test_ignore_same_filename_at_all_depths(self) -> None:
        """Test that a specific filename is ignored regardless of nesting depth."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "dist.txt").write_text("root")
            sub = Path(tmpdir) / "src"
            sub.mkdir()
            (sub / "dist.txt").write_text("sub")
            nested = sub / "lib"
            nested.mkdir()
            (nested / "dist.txt").write_text("nested")
            result = Scanner(tmpdir, ignore=("dist.txt",), no_gitignore=True).scan()
            assert result.total_files == 0

    def test_ignore_mixed_files_and_directories(self) -> None:
        """Test that mixed ignore patterns covering files and directories both apply."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "main.py").write_text("main")
            (Path(tmpdir) / "test.py").write_text("test")
            (Path(tmpdir) / "build.log").write_text("log")
            build_dir = Path(tmpdir) / "build"
            build_dir.mkdir()
            (build_dir / "output.o").write_text("output")
            result = Scanner(
                tmpdir, ignore=("*.log", "build"), no_gitignore=True
            ).scan()
            assert result.total_files == 2
            names = {f.name for f in result.scanned_files}
            assert names == {"main.py", "test.py"}
