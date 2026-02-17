"""Tests for TableFormatter edge cases."""

from datetime import datetime
from pathlib import Path

from statsvy.data.metrics import Metrics
from statsvy.formatters.table_formatter import TableFormatter


class TestTableFormatterEdgeCases:
    """Test suite for edge cases in CLI formatting."""

    def test_format_with_very_large_file_count(self) -> None:
        """Tests that the formatter handles very large numbers correctly."""
        metrics = Metrics(
            name="huge_project",
            path=Path("/test"),
            timestamp=datetime.now(),
            total_files=999999,
            total_size_bytes=0,
            total_size_kb=0,
            total_size_mb=0,
            lines_by_lang={},
            comment_lines_by_lang={},
            blank_lines_by_lang={},
            lines_by_category={},
            comment_lines=0,
            blank_lines=0,
            total_lines=0,
        )
        formatter = TableFormatter()
        result = formatter.format(metrics)
        assert "999,999" in result
