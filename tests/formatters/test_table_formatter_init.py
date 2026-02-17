"""Tests for TableFormatter initialization."""

from statsvy.formatters.table_formatter import TableFormatter


class TestTableFormatterInitialization:
    """Test suite for CliFormatter initialization."""

    def test_formatter_can_be_instantiated(self) -> None:
        """Tests that the CliFormatter class can be instantiated."""
        formatter = TableFormatter()
        assert formatter is not None
