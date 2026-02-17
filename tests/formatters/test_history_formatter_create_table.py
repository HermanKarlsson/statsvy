"""Tests for HistoryFormatter._create_history_table() method."""

from rich.table import Table

from statsvy.formatters.history_formatter import (
    HistoryEntry,
    HistoryFormatter,
)

_DEFAULT_CATEGORIES: dict[str, int] = {
    "programming": 5_000,
    "data": 4_000,
    "prose": 1_000,
    "unknown": 0,
}


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
            else dict(_DEFAULT_CATEGORIES),
            "lines_by_language": {},
        },
    }


SINGLE_ENTRY: list[HistoryEntry] = [_make_entry()]

TWO_ENTRIES: list[HistoryEntry] = [
    _make_entry(
        time="2026-02-13 10:00:00",
        total_files=50,
        total_lines=500,
        categories={"programming": 300, "data": 150, "prose": 50, "unknown": 0},
    ),
    _make_entry(
        time="2026-02-13 11:00:00",
        total_files=52,
        total_lines=600,
        categories={"programming": 350, "data": 200, "prose": 50, "unknown": 0},
    ),
]


class TestCreateHistoryTable:
    """Tests for :meth:`HistoryFormatter._create_history_table`."""

    def test_returns_rich_table(self) -> None:
        """Should return a Rich :class:`~rich.table.Table` object."""
        formatter = HistoryFormatter()
        table = formatter._create_history_table(SINGLE_ENTRY)
        assert isinstance(table, Table)

    def test_row_count_matches_entries(self) -> None:
        """The table should have exactly as many rows as entries."""
        formatter = HistoryFormatter()
        table = formatter._create_history_table(TWO_ENTRIES)
        assert table.row_count == len(TWO_ENTRIES)

    def test_single_entry_row_count(self) -> None:
        """A single entry should produce exactly one row."""
        formatter = HistoryFormatter()
        table = formatter._create_history_table(SINGLE_ENTRY)
        assert table.row_count == 1

    def test_entry_missing_total_size_defaults_to_dash(self) -> None:
        """Entries without ``total_size`` should show ``-`` without raising."""
        entry: HistoryEntry = _make_entry()
        del entry["metrics"]["total_size"]
        formatter = HistoryFormatter()
        table = formatter._create_history_table([entry])
        assert table.row_count == 1

    def test_entry_missing_category_defaults_to_zero(self) -> None:
        """Missing category keys should default to ``0`` without raising."""
        entry: HistoryEntry = _make_entry()
        entry["metrics"]["lines_by_category"] = {}
        formatter = HistoryFormatter()
        table = formatter._create_history_table([entry])
        assert table.row_count == 1
