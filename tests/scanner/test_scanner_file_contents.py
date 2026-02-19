"""Tests for Scanner providing pre-read file contents in ScanResult."""

from pathlib import Path
from unittest.mock import MagicMock

from statsvy.core.scanner import Scanner
from statsvy.data.config import Config


def test_scan_populates_file_contents_for_text_files(tmp_path: Path) -> None:
    """Scanner.scan should include text contents for non-binary files."""
    (tmp_path / "a.py").write_text("print(1)\n# comment\n")
    (tmp_path / "b.png").write_bytes(b"\x00\x01\x02")

    mock_tracker = MagicMock()
    mock_tracker.is_tracking_io.return_value = True

    scanner = Scanner(
        path=tmp_path,
        no_gitignore=True,
        config=Config.default(),
        perf_tracker=mock_tracker,
    )

    result = scanner.scan()

    assert result.file_contents is not None
    # text file should be present and match on-disk content
    assert (tmp_path / "a.py") in result.file_contents
    assert result.file_contents[tmp_path / "a.py"].startswith("print(1)")

    # binary-like file (.png is in default binary_extensions) should not have text
    assert (tmp_path / "b.png") not in result.file_contents or result.file_contents[
        tmp_path / "b.png"
    ] is None

    # I/O should have been recorded by the scanner for the text file
    assert mock_tracker.record_io.called


def test_scan_does_not_store_contents_for_ignored_or_skipped_files(
    tmp_path: Path,
) -> None:
    """Files skipped by size/ignore should not be present in file_contents."""
    a = tmp_path / "large.txt"
    # write a large file exceeding default max (but default limits allow large files);
    # instead simulate skip by providing ignore pattern
    a.write_text("line\n" * 3)

    scanner = Scanner(
        path=tmp_path, ignore=("large.txt",), no_gitignore=True, config=Config.default()
    )
    result = scanner.scan()

    # file_contents may be None when nothing was scanned — ensure the
    # ignored file is not present when a mapping exists.
    assert (result.file_contents is None) or (a not in result.file_contents)
