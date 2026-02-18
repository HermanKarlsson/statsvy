"""Tests for duplicate-file detection in Scanner."""

from dataclasses import replace
from pathlib import Path

from statsvy.core.scanner import Scanner
from statsvy.data.config import Config


class TestDuplicateDetection:
    """Tests for duplicate-detection behaviour of Scanner."""

    @staticmethod
    def write_file(path: Path, content: str) -> None:
        """Write text content to the given path using UTF-8 encoding."""
        path.write_text(content, encoding="utf-8")

    def test_no_duplicate_detection_by_default(self, tmp_path: Path) -> None:
        """Small files under the duplicate threshold are not reported as duplicates.

        Scanner always checks duplicates, but the default `duplicate_threshold_bytes`
        prevents hashing of very small files (hence no duplicates for tiny files).
        """
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        self.write_file(a, "hello\n")
        self.write_file(b, "hello\n")

        scanner = Scanner(tmp_path, config=Config.default())
        result = scanner.scan()

        assert result.scanned_files  # both files discovered
        assert result.duplicate_files == ()

    def test_detects_duplicate_files_when_enabled(self, tmp_path: Path) -> None:
        """Scanner should record duplicate files when enabled in config."""
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        self.write_file(a, "same content\n")
        self.write_file(b, "same content\n")

        base_cfg = Config.default()
        files_cfg = replace(base_cfg.files, duplicate_threshold_bytes=1)
        cfg = replace(base_cfg, files=files_cfg)

        scanner = Scanner(tmp_path, config=cfg)
        result = scanner.scan()

        # both files are present in scanned_files, and exactly one should be
        # reported as duplicate (order from rglob is not guaranteed)
        assert set(result.scanned_files) == {a, b}
        assert len(result.duplicate_files) == 1
        assert result.duplicate_files[0] in {a, b}
