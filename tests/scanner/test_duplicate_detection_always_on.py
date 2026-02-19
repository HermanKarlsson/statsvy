"""Verify scanner always detects duplicates (core behaviour)."""

from pathlib import Path

from statsvy.core.scanner import Scanner
from statsvy.data.config import Config


def write_file(path: Path, content: str) -> None:
    """Write text to a file using UTF-8 encoding (test helper)."""
    path.write_text(content, encoding="utf-8")


def test_scanner_detects_duplicates_even_if_config_disabled(tmp_path: Path) -> None:
    """Scanner always detects duplicates; configuration flag was removed."""
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"

    # write files larger than default duplicate_threshold_bytes (1024)
    big_content = "x" * 2048
    write_file(a, big_content)
    write_file(b, big_content)

    # use default config — duplicate detection is core behaviour
    scanner = Scanner(tmp_path, config=Config.default())
    result = scanner.scan()

    assert set(result.scanned_files) == {a, b}
    assert len(result.duplicate_files) == 1
    assert result.duplicate_files[0] in {a, b}
