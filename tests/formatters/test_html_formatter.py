"""Unit tests for the HtmlFormatter class."""

from html import escape
from unittest.mock import MagicMock

from statsvy.data.dependency import Dependency
from statsvy.data.project_info import DependencyInfo
from statsvy.formatters.html_formatter import HtmlFormatter


class TestHtmlFormatter:
    """Tests verifying basic HTML output structure."""

    def test_basic_structure(self, minimal_metrics: MagicMock) -> None:
        """Output should be a complete HTML document with head and body."""
        fmt = HtmlFormatter()
        result = fmt.format(minimal_metrics)
        assert result.strip().startswith("<!DOCTYPE html>")
        assert "<html" in result and "</html>" in result
        assert "<body>" in result and "</body>" in result

    def test_summary_table(self, minimal_metrics: MagicMock) -> None:
        """Summary section should include project name and total lines."""
        fmt = HtmlFormatter()
        result = fmt.format(minimal_metrics)
        assert "<h2>Project Statistics</h2>" in result
        assert "Total Lines" in result
        assert escape(minimal_metrics.name) in result

    def test_category_and_language_tables(self, full_metrics: MagicMock) -> None:
        """When metrics contain category/lang data, tables are rendered."""
        fmt = HtmlFormatter()
        result = fmt.format(full_metrics)
        assert "Lines of Code by Type" in result
        assert "Lines of Code by Language" in result

    def test_escaping(self, minimal_metrics: MagicMock) -> None:
        """Special characters in names/paths should be escaped."""
        minimal_metrics.name = "<proj>&"  # some chars needing escape
        fmt = HtmlFormatter()
        result = fmt.format(minimal_metrics)
        assert "<proj>" not in result
        assert escape(minimal_metrics.name) in result

    def test_dependencies_section(self, minimal_metrics: MagicMock) -> None:
        """Dependencies are included by default with package listing."""
        dep = Dependency(name="foo", version="1.0", category="prod", source_file="p1")
        minimal_metrics.dependencies = DependencyInfo(
            dependencies=(dep,),
            prod_count=1,
            dev_count=0,
            optional_count=0,
            total_count=1,
            sources=("p1",),
            conflicts=(),
        )

        fmt = HtmlFormatter()
        result = fmt.format(minimal_metrics)
        assert "<h2>Dependencies</h2>" in result
        assert "foo" in result
