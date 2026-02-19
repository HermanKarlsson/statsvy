"""Test suite for the Analyzer module sequential use.

Tests confirm Analyzer can be used multiple times without state leakage.
"""

import tempfile
from pathlib import Path

import pytest

from statsvy.core.analyzer import Analyzer
from statsvy.core.scanner import Scanner
from statsvy.data.scan_result import ScanResult


def _make_scan_result(files: list[Path], size: int = 0) -> ScanResult:
    """Build a ScanResult from a list of file paths.

    Args:
        files: List of Path objects to include.
        size: Total size in bytes to report.

    Returns:
        A ScanResult populated with the given files.
    """
    return ScanResult(
        total_files=len(files),
        total_size_bytes=size,
        scanned_files=tuple(files),
    )


class TestAnalyzerSequentialUse:
    """Tests confirming Analyzer can be used multiple times without state leakage."""

    def test_second_analysis_does_not_affect_first_result(self) -> None:
        """Test that calling analyze() twice yields two independent Metrics objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = Analyzer("t", Path(tmpdir))
            r1 = analyzer.analyze(
                ScanResult(total_files=5, total_size_bytes=100, scanned_files=())
            )
            r2 = analyzer.analyze(
                ScanResult(total_files=10, total_size_bytes=200, scanned_files=())
            )
            assert r1.total_files == 5
            assert r2.total_files == 10

    def test_lines_do_not_accumulate_across_calls(self) -> None:
        """Test that each analyze() call starts with a fresh line count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "a.py"
            f.write_text("line1\nline2\n")
            analyzer = Analyzer("t", Path(tmpdir))
            sr = _make_scan_result([f])
            r1 = analyzer.analyze(sr)
            r2 = analyzer.analyze(sr)
            assert r1.total_lines == r2.total_lines == 2

    def test_scanner_reads_files_once_and_analyzer_uses_cached_data(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Ensure Scanner reads files once and Analyzer uses cached data.

        Scanner has provided per-file metadata. This prevents redundant reads —
        files should be read during scan and then consumed from the provided
        metadata by Analyzer.
        """
        # Prepare two source files
        a = tmp_path / "a.py"
        b = tmp_path / "b.js"
        a.write_text("x\ny\n")
        b.write_text("1\n2\n3\n")

        # Count file read operations by wrapping Path.read_text, read_bytes and open
        orig_read_text = Path.read_text
        orig_read_bytes = Path.read_bytes
        orig_open = Path.open
        counts = {"read_text": 0, "read_bytes": 0, "open": 0}

        def counted_read_text(
            self: Path,
            encoding: str | None = None,
            errors: str | None = None,
        ) -> str:
            if self in {a, b}:
                counts["read_text"] += 1
            return orig_read_text(self, encoding=encoding, errors=errors)

        def counted_read_bytes(self: Path) -> bytes:
            if self in {a, b}:
                counts["read_bytes"] += 1
            return orig_read_bytes(self)

        def counted_open(
            self: Path,
            mode: str = "r",
            buffering: int = -1,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
        ) -> object:
            if self in {a, b}:
                counts["open"] += 1
            return orig_open(self, mode, buffering, encoding, errors, newline)

        monkeypatch.setattr(Path, "read_text", counted_read_text)
        monkeypatch.setattr(Path, "read_bytes", counted_read_bytes)
        monkeypatch.setattr(Path, "open", counted_open)

        # Run Scanner.scan() — this should perform the file reads
        scanner = Scanner(tmp_path)
        scan_result = scanner.scan()

        # At least one read must have happened during scan (per file)
        assert counts["read_text"] + counts["read_bytes"] + counts["open"] >= 2

        # Reset counters and run Analyzer.analyze(scan_result)
        counts["read_text"] = counts["read_bytes"] = counts["open"] = 0
        analyzer = Analyzer("t", tmp_path)
        analyzer.analyze(scan_result)

        # Analyzer should not reopen files when file_data is present
        assert counts["read_text"] + counts["read_bytes"] + counts["open"] == 0
