"""Tests for binary file filtering in analyzer."""

import tempfile
from dataclasses import replace
from pathlib import Path

from statsvy.core.analyzer import Analyzer
from statsvy.core.scanner import Scanner
from statsvy.data.config import Config


class TestAnalyzerBinaryFileFiltering:
    """Test that analyzer properly skips binary files based on extension."""

    def test_analyzer_skips_binary_files(self) -> None:
        """Test that files with binary extensions are not analyzed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create text file
            text_file = tmp_path / "test.py"
            text_file.write_text("print('hello')\n")

            # Create binary files
            exe_file = tmp_path / "program.exe"
            exe_file.write_bytes(b"\x00\x01\x02\x03")

            jpg_file = tmp_path / "image.jpg"
            jpg_file.write_bytes(b"\xff\xd8\xff")

            # Scan directory
            scanner = Scanner(tmp_path, no_gitignore=True)
            scan_result = scanner.scan()

            # Analyze with default config (includes binary_extensions)
            config = Config.default()
            analyzer = Analyzer(
                name="test",
                path=tmp_path,
                config=config,
            )
            metrics = analyzer.analyze(scan_result)

            # Should only analyze the .py file
            # Binary files should be in the scan but not analyzed
            assert scan_result.total_files == 3  # All files scanned
            assert metrics.total_lines == 1  # Only .py file analyzed

    def test_analyzer_processes_files_not_in_binary_extensions(self) -> None:
        """Test that files without binary extensions are analyzed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create various text files
            (tmp_path / "script.py").write_text("line1\nline2\n")
            (tmp_path / "script.js").write_text("var x = 1;\n")
            (tmp_path / "README.md").write_text("# Title\n\nContent\n")

            scanner = Scanner(tmp_path, no_gitignore=True)
            scan_result = scanner.scan()

            analyzer = Analyzer(
                name="test",
                path=tmp_path,
                config=Config.default(),
            )
            metrics = analyzer.analyze(scan_result)

            # All three files should be analyzed (2 + 1 + 3 lines)
            assert metrics.total_lines == 6

    def test_analyzer_respects_custom_binary_extensions(self) -> None:
        """Test that custom binary_extensions are respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create files
            (tmp_path / "data.txt").write_text("line1\nline2\n")
            (tmp_path / "data.custom").write_text("line3\nline4\n")

            # Create config with custom binary extension
            config = Config.default()
            scan_config = replace(
                config.scan,
                binary_extensions=(*config.scan.binary_extensions, ".custom"),
            )
            config = replace(config, scan=scan_config)

            scanner = Scanner(tmp_path, no_gitignore=True, config=config)
            scan_result = scanner.scan()

            analyzer = Analyzer(
                name="test",
                path=tmp_path,
                config=config,
            )
            metrics = analyzer.analyze(scan_result)

            # Only .txt file should be analyzed (.custom is now binary)
            assert metrics.total_lines == 2

    def test_analyzer_case_insensitive_extension_matching(self) -> None:
        """Test that binary extension matching is case-insensitive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create files with different case extensions
            (tmp_path / "program.EXE").write_bytes(b"\x00\x01")
            (tmp_path / "image.JPG").write_bytes(b"\xff\xd8")
            (tmp_path / "script.PY").write_text("print('test')\n")

            scanner = Scanner(tmp_path, no_gitignore=True)
            scan_result = scanner.scan()

            analyzer = Analyzer(
                name="test",
                path=tmp_path,
                config=Config.default(),
            )
            metrics = analyzer.analyze(scan_result)

            # .EXE and .JPG should be skipped (case-insensitive)
            # Only .PY should be analyzed
            assert metrics.total_lines == 1

    def test_analyzer_mixed_binary_and_text_files(self) -> None:
        """Test analyzer with a mix of binary and text files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Text files
            (tmp_path / "source.py").write_text("line1\n")
            (tmp_path / "source.js").write_text("line2\n")
            (tmp_path / "README.md").write_text("line3\n")

            # Binary files (default extensions)
            (tmp_path / "app.exe").write_bytes(b"\x00\x01")
            (tmp_path / "lib.dll").write_bytes(b"\x00\x02")
            (tmp_path / "cache.pyc").write_bytes(b"\x00\x03")
            (tmp_path / "pic.png").write_bytes(b"\x89PNG")
            (tmp_path / "archive.zip").write_bytes(b"PK\x03\x04")

            scanner = Scanner(tmp_path, no_gitignore=True)
            scan_result = scanner.scan()

            analyzer = Analyzer(
                name="test",
                path=tmp_path,
                config=Config.default(),
            )
            metrics = analyzer.analyze(scan_result)

            # Should scan all 8 files
            assert scan_result.total_files == 8

            # Should only analyze 3 text files
            assert metrics.total_lines == 3

    def test_analyzer_no_files_match_binary_extensions(self) -> None:
        """Test analyzer when no files have binary extensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Only text files
            (tmp_path / "file1.txt").write_text("a\n")
            (tmp_path / "file2.md").write_text("b\n")
            (tmp_path / "file3.py").write_text("c\n")

            scanner = Scanner(tmp_path, no_gitignore=True)
            scan_result = scanner.scan()

            analyzer = Analyzer(
                name="test",
                path=tmp_path,
                config=Config.default(),
            )
            metrics = analyzer.analyze(scan_result)

            # All files should be analyzed
            assert metrics.total_lines == 3

    def test_analyzer_all_files_are_binary(self) -> None:
        """Test analyzer when all files are binary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Only binary files
            (tmp_path / "app.exe").write_bytes(b"\x00")
            (tmp_path / "lib.dll").write_bytes(b"\x01")
            (tmp_path / "img.jpg").write_bytes(b"\x02")

            scanner = Scanner(tmp_path, no_gitignore=True)
            scan_result = scanner.scan()

            analyzer = Analyzer(
                name="test",
                path=tmp_path,
                config=Config.default(),
            )
            metrics = analyzer.analyze(scan_result)

            # Files scanned but nothing analyzed
            assert scan_result.total_files == 3
            assert metrics.total_lines == 0
