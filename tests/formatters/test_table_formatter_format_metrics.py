"""Tests for TableFormatter format_metrics functionality."""

from statsvy.data.metrics import Metrics
from statsvy.formatters.table_formatter import TableFormatter


class TestTableFormatterFormatMetrics:
    """Test suite for formatting Metrics objects into CLI output."""

    def test_format_returns_string(self, sample_metrics: Metrics) -> None:
        """Tests that the format method returns a string object."""
        formatter = TableFormatter()
        result = formatter.format(sample_metrics)
        assert isinstance(result, str)

    def test_format_contains_project_name(self, sample_metrics: Metrics) -> None:
        """Tests that the formatted output contains the project name."""
        formatter = TableFormatter()
        result = formatter.format(sample_metrics)
        assert sample_metrics.name in result

    def test_format_contains_total_files(self, sample_metrics: Metrics) -> None:
        """Tests that the formatted output contains the total file count."""
        formatter = TableFormatter()
        result = formatter.format(sample_metrics)
        assert f"{sample_metrics.total_files:,}" in result

    def test_format_contains_file_size(self, sample_metrics: Metrics) -> None:
        """Tests that the formatted output contains file size information."""
        formatter = TableFormatter()
        result = formatter.format(sample_metrics)
        assert "MB" in result

    def test_format_contains_total_lines(self, sample_metrics: Metrics) -> None:
        """Tests that the formatted output contains the total lines of code."""
        formatter = TableFormatter()
        result = formatter.format(sample_metrics)
        assert f"{sample_metrics.total_lines:,}" in result

    def test_format_contains_timestamp(self, sample_metrics: Metrics) -> None:
        """Tests that the formatted output contains the timestamp year."""
        formatter = TableFormatter()
        result = formatter.format(sample_metrics)
        assert "2024" in result

    def test_format_with_empty_metrics(self, empty_metrics: Metrics) -> None:
        """Tests that the formatter handles empty metrics gracefully.

        Verifies that '0' is displayed and no errors occur.
        """
        formatter = TableFormatter()
        result = formatter.format(empty_metrics)
        assert isinstance(result, str)
        assert empty_metrics.name in result
        assert "0" in result
