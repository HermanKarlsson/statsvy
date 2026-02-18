"""Tests for Analyzer I/O instrumentation."""

from pathlib import Path
from unittest.mock import MagicMock

from statsvy.core.analyzer import Analyzer
from statsvy.data.config import Config


def test_count_file_lines_records_io(tmp_path: Path) -> None:
    """Ensure _count_file_lines records an I/O event when tracker enabled."""
    file_path = tmp_path / "sample.py"
    content = "line1\nline2\nline3\n"
    file_path.write_text(content)

    mock_tracker = MagicMock()
    mock_tracker.is_tracking_io.return_value = True

    analyzer = Analyzer(
        name="test",
        path=tmp_path,
        config=Config.default(),
        perf_tracker=mock_tracker,
    )

    count = analyzer._count_file_lines(file_path)

    assert count == 3
    assert mock_tracker.record_io.called
    recorded_args = mock_tracker.record_io.call_args[1]
    assert recorded_args.get("bytes_read", 0) >= len(content)
    assert recorded_args.get("elapsed_seconds", 0) >= 0


def test_process_file_records_io_twice(tmp_path: Path) -> None:
    """Verify _process_file records I/O for both counting and file-read."""
    file_path = tmp_path / "sample2.py"
    content = "# comment\nprint(1)\n"
    file_path.write_text(content)

    mock_tracker = MagicMock()
    mock_tracker.is_tracking_io.return_value = True

    analyzer = Analyzer(
        name="test",
        path=tmp_path,
        config=Config.default(),
        perf_tracker=mock_tracker,
    )

    metrics_data: dict = {
        "lines_by_lang": {},
        "lines_by_category": {},
        "total_lines": 0,
        "comment_lines": 0,
        "blank_lines": 0,
        "comment_lines_by_lang": {},
        "blank_lines_by_lang": {},
    }

    analyzer._process_file(file_path, metrics_data)

    # _count_file_lines and the read_text each record an I/O operation
    assert mock_tracker.record_io.call_count >= 2
