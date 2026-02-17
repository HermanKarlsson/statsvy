"""Tests for MarkdownFormatter."""

from unittest.mock import MagicMock

from statsvy.formatters.markdown_formatter import MarkdownFormatter


class TestMarkdownFormatter:
    """Tests for MarkdownFormatter."""

    def test_returns_string(self, minimal_metrics: MagicMock) -> None:
        """Return type must be str."""
        assert isinstance(MarkdownFormatter().format(minimal_metrics), str)

    def test_heading_contains_project_name(self, minimal_metrics: MagicMock) -> None:
        """The H1 heading must include the project name."""
        result = MarkdownFormatter().format(minimal_metrics)
        assert "# Scan: my_project" in result

    def test_summary_table_fields(self, minimal_metrics: MagicMock) -> None:
        """Summary section must contain all key fields."""
        result = MarkdownFormatter().format(minimal_metrics)
        assert "## Project Statistics" in result
        assert "/home/user/project" in result
        assert "2024-06-01" in result
        assert "42" in result
        assert "1.5 MB" in result
        assert "1,000" in result

    def test_no_category_section_when_empty(self, minimal_metrics: MagicMock) -> None:
        """Category section must not appear when there is no category data."""
        result = MarkdownFormatter().format(minimal_metrics)
        assert "Lines of Code by Type" not in result

    def test_no_language_section_when_empty(self, minimal_metrics: MagicMock) -> None:
        """Language section must not appear when there is no language data."""
        result = MarkdownFormatter().format(minimal_metrics)
        assert "Lines of Code by Language" not in result

    def test_category_section_present(self, full_metrics: MagicMock) -> None:
        """Category section must appear and contain category names."""
        result = MarkdownFormatter().format(full_metrics)
        assert "## Lines of Code by Type" in result
        assert "Source" in result
        assert "Test" in result
        assert "Unknown" in result

    def test_language_section_present(self, full_metrics: MagicMock) -> None:
        """Language section must appear and list all languages."""
        result = MarkdownFormatter().format(full_metrics)
        assert "## Lines of Code by Language" in result
        assert "Python" in result
        assert "YAML" in result

    def test_category_percentages(self, full_metrics: MagicMock) -> None:
        """Category rows must include percentage values."""
        result = MarkdownFormatter().format(full_metrics)
        assert "70.0%" in result

    def test_language_code_columns(self, full_metrics: MagicMock) -> None:
        """Language table must expose the code/comments/blank breakdown."""
        result = MarkdownFormatter().format(full_metrics)
        assert "230" in result

    def test_table_has_markdown_pipes(self, full_metrics: MagicMock) -> None:
        """Tables must use the pipe character as column delimiter."""
        result = MarkdownFormatter().format(full_metrics)
        assert "|" in result

    def test_zero_total_lines(self, zero_lines_metrics: MagicMock) -> None:
        """Formatter must not raise when total_lines is zero."""
        result = MarkdownFormatter().format(zero_lines_metrics)
        assert "0.0%" in result

    def test_sorted_by_line_count_descending(self, full_metrics: MagicMock) -> None:
        """Both tables must list entries in descending line-count order."""
        result = MarkdownFormatter().format(full_metrics)
        python_pos = result.index("Python")
        yaml_pos = result.index("YAML")
        assert python_pos < yaml_pos  # Python (300) before YAML (200)
