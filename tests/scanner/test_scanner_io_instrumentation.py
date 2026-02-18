"""Tests for Scanner I/O instrumentation."""

from pathlib import Path
from unittest.mock import MagicMock

from statsvy.core.scanner import Scanner
from statsvy.data.config import Config


def test_file_hash_records_io(tmp_path: Path) -> None:
    """Ensure Scanner._file_hash records I/O timing and byte count."""
    file_path = tmp_path / "data.bin"
    data = b"0123456789" * 10
    file_path.write_bytes(data)

    mock_tracker = MagicMock()
    mock_tracker.is_tracking_io.return_value = True

    scanner = Scanner(path=tmp_path, config=Config.default(), perf_tracker=mock_tracker)

    digest = scanner._file_hash(file_path)

    assert digest
    assert mock_tracker.record_io.called
    args = mock_tracker.record_io.call_args[1]
    assert args.get("bytes_read") == len(data)
    assert args.get("elapsed_seconds") >= 0
