"""Tests for the _parse_time helper function."""

from datetime import datetime

from statsvy.formatters.history_formatter import (
    HistoryEntry,
    _parse_time,
)


def _make_entry(
    time: str = "2026-02-13 15:04:45",
    total_files: int = 50,
    total_lines: int = 500,
    total_size: str = "0 MB (400 KB)",
    categories: dict[str, int] | None = None,
) -> HistoryEntry:
    """Build a minimal history entry dict for use in tests.

    Args:
        time: Timestamp string in ``%Y-%m-%d %H:%M:%S`` format.
        total_files: Number of files in the scan.
        total_lines: Total line count for the scan.
        total_size: Human-readable size string.
        categories: Mapping of category name to line count.

    Returns:
        A history entry dict matching the structure produced by the scanner.
    """
    default_categories: dict[str, int] = {
        "programming": 5_000,
        "data": 4_000,
        "prose": 1_000,
        "unknown": 0,
    }
    return {
        "time": time,
        "metrics": {
            "name": "/home/user/project",
            "path": "/home/user/project",
            "timestamp": time[:10],
            "total_files": total_files,
            "total_size": total_size,
            "total_lines": total_lines,
            "lines_by_category": categories
            if categories is not None
            else dict(default_categories),
            "lines_by_language": {},
        },
    }


class TestParseTime:
    """Tests for the :func:`_parse_time` helper."""

    def test_returns_correct_datetime(self) -> None:
        """Should parse the ``time`` field into the expected datetime."""
        entry = _make_entry(time="2026-02-13 15:04:45")
        result = _parse_time(entry)
        assert result == datetime(2026, 2, 13, 15, 4, 45)

    def test_midnight(self) -> None:
        """Should handle midnight timestamps without error."""
        entry = _make_entry(time="2026-01-01 00:00:00")
        result = _parse_time(entry)
        assert result == datetime(2026, 1, 1, 0, 0, 0)
