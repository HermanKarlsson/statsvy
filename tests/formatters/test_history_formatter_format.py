"""Tests for HistoryFormatter.format() method."""

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

THREE_ENTRIES: list[HistoryEntry] = [
    _make_entry(
        time="2026-02-13 09:00:00",
        total_lines=400,
        categories={"programming": 200, "data": 150, "prose": 50, "unknown": 0},
    ),
    _make_entry(
        time="2026-02-13 10:00:00",
        total_lines=500,
        categories={"programming": 300, "data": 150, "prose": 50, "unknown": 0},
    ),
    _make_entry(
        time="2026-02-13 11:00:00",
        total_lines=450,
        categories={"programming": 250, "data": 150, "prose": 50, "unknown": 0},
    ),
]


class TestHistoryFormatterFormat:
    """Tests for :meth:`HistoryFormatter.format`."""

    def test_returns_string(self) -> None:
        """``format`` should always return a ``str``."""
        formatter = HistoryFormatter()
        result = formatter.format(SINGLE_ENTRY)
        assert isinstance(result, str)

    def test_empty_list_returns_string(self) -> None:
        """``format`` should not raise when given an empty entry list."""
        formatter = HistoryFormatter()
        result = formatter.format([])
        assert isinstance(result, str)

    def test_empty_list_mentions_no_history(self) -> None:
        """The output for an empty list should indicate there is nothing to show."""
        formatter = HistoryFormatter()
        result = formatter.format([])
        assert "No history entries" in result

    def test_header_panel_present(self) -> None:
        """Output should include the ``Scan History`` header text."""
        formatter = HistoryFormatter()
        result = formatter.format(SINGLE_ENTRY)
        assert "Scan History" in result

    def test_timestamp_present(self) -> None:
        """The formatted timestamp should appear in the output."""
        formatter = HistoryFormatter()
        result = formatter.format(SINGLE_ENTRY)
        assert "2026-02-13" in result

    def test_total_lines_present(self) -> None:
        """Total line count should appear in the rendered output."""
        formatter = HistoryFormatter()
        result = formatter.format(SINGLE_ENTRY)
        assert "500" in result

    def test_first_row_has_no_delta(self) -> None:
        """The very first row should display ``-`` (no delta) for all Δ columns."""
        formatter = HistoryFormatter()
        result = formatter.format(SINGLE_ENTRY)
        assert "-" in result

    def test_second_row_has_positive_delta(self) -> None:
        """A row where lines increased should contain a ``+`` delta string."""
        formatter = HistoryFormatter()
        result = formatter.format(TWO_ENTRIES)
        assert "+" in result

    def test_decreasing_entry_has_negative_delta(self) -> None:
        """A row where lines decreased should contain a ``-`` delta string."""
        formatter = HistoryFormatter()
        result = formatter.format(THREE_ENTRIES)
        assert "-" in result

    def test_multiple_entries_all_indexed(self) -> None:
        """Every entry should receive a sequential row index starting at 1."""
        formatter = HistoryFormatter()
        result = formatter.format(THREE_ENTRIES)
        for idx in ("1", "2", "3"):
            assert idx in result

    def test_size_string_present(self) -> None:
        """The total_size value should appear somewhere in the output."""
        formatter = HistoryFormatter()
        result = formatter.format(SINGLE_ENTRY)
        assert "KB" in result
