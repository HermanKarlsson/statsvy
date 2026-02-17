"""Tests for min/max file-size filtering in Scanner."""

import tempfile
from dataclasses import replace
from pathlib import Path

from statsvy.core.scanner import Scanner
from statsvy.data.config import Config


class TestScannerSizeFiltering:
    """Verify files outside configured size bounds are skipped."""

    def test_scanner_skips_files_larger_than_max_size(self) -> None:
        """Files larger than scan.max_file_size_mb should be skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create a small non-empty file
            (tmp_path / "file.txt").write_text("small content")

            # Configure max size to 0 MB -> only zero-byte files allowed
            config = Config.default()
            scan_cfg = replace(config.scan, max_file_size_mb=0)
            cfg = replace(config, scan=scan_cfg)

            scanner = Scanner(tmp_path, no_gitignore=True, config=cfg)
            result = scanner.scan()

            # The non-empty file is larger than 0 bytes -> should be skipped
            assert result.total_files == 0
            assert result.total_size_bytes == 0

    def test_scanner_skips_files_smaller_than_min_size(self) -> None:
        """Files smaller than scan.min_file_size_mb should be skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create a small file (few bytes)
            (tmp_path / "small.txt").write_text("tiny")

            # Set min size to 1 MB -> small file should be skipped
            config = Config.default()
            scan_cfg = replace(config.scan, min_file_size_mb=1)
            cfg = replace(config, scan=scan_cfg)

            scanner = Scanner(tmp_path, no_gitignore=True, config=cfg)
            result = scanner.scan()

            assert result.total_files == 0
            assert result.total_size_bytes == 0

    def test_scanner_includes_file_within_min_max_range(self) -> None:
        """A file whose size is within [min, max] (inclusive) is included."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create a 1 MiB file
            size_bytes = 1024 * 1024
            (tmp_path / "ok.bin").write_bytes(b"a" * size_bytes)

            config = Config.default()
            scan_cfg = replace(config.scan, min_file_size_mb=1, max_file_size_mb=1)
            cfg = replace(config, scan=scan_cfg)

            scanner = Scanner(tmp_path, no_gitignore=True, config=cfg)
            result = scanner.scan()

            assert result.total_files == 1
            assert result.total_size_bytes == size_bytes

    def test_scanner_decimal_mb_threshold(self) -> None:
        """Scanner should accept decimal MB thresholds (e.g. 1.5 MB)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create a 1.5 MiB file
            size_bytes = int(1.5 * 1024 * 1024)
            (tmp_path / "ok.bin").write_bytes(b"a" * size_bytes)

            config = Config.default()
            scan_cfg = replace(config.scan, min_file_size_mb=1.5, max_file_size_mb=2.0)
            cfg = replace(config, scan=scan_cfg)

            scanner = Scanner(tmp_path, no_gitignore=True, config=cfg)
            result = scanner.scan()

            assert result.total_files == 1
            assert result.total_size_bytes == size_bytes
