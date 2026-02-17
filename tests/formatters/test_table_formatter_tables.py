"""Tests for TableFormatter output tables."""

from statsvy.data.metrics import Metrics
from statsvy.formatters.table_formatter import TableFormatter


class TestTableFormatterTables:
    """Test suite for specific table outputs (category and language)."""

    def test_format_includes_category_breakdown(self, sample_metrics: Metrics) -> None:
        """Tests that the output includes the category breakdown table."""
        formatter = TableFormatter()
        result = formatter.format(sample_metrics)
        for category in sample_metrics.lines_by_category:
            assert category.title() in result

    def test_format_with_empty_category_dict(self, empty_metrics: Metrics) -> None:
        """Tests that the category table is omitted when no data exists."""
        formatter = TableFormatter()
        result = formatter.format(empty_metrics)
        assert "Lines of Code by Type" not in result

    def test_format_includes_language_breakdown(self, sample_metrics: Metrics) -> None:
        """Tests that the output includes the language breakdown table."""
        formatter = TableFormatter()
        result = formatter.format(sample_metrics)
        for language in sample_metrics.lines_by_lang:
            assert language in result

    def test_format_with_empty_language_dict(self, empty_metrics: Metrics) -> None:
        """Tests that the language table is omitted when no data exists."""
        formatter = TableFormatter()
        result = formatter.format(empty_metrics)
        assert "Lines of Code by Language" not in result

    def test_tables_calculate_percentages(self, sample_metrics: Metrics) -> None:
        """Tests that percentage values are calculated and displayed."""
        formatter = TableFormatter()
        result = formatter.format(sample_metrics)
        assert "%" in result
