"""Tests for display customization options (truncate paths, percentages)."""

from datetime import datetime
from pathlib import Path

import pytest

from statsvy.data.config import DisplayConfig
from statsvy.data.metrics import Metrics
from statsvy.formatters.markdown_formatter import MarkdownFormatter
from statsvy.formatters.table_formatter import TableFormatter


@pytest.fixture
def sample_metrics() -> Metrics:
    """Create sample metrics for testing display customization."""
    return Metrics(
        name="test_project",
        path=Path("/home/user/projects/statsvy/src/module"),
        timestamp=datetime(2024, 2, 8, 10, 30, 45),
        total_files=42,
        total_size_bytes=1048576,
        total_size_kb=1024,
        total_size_mb=1,
        lines_by_lang={"Python": 5000, "JavaScript": 2000},
        comment_lines_by_lang={"Python": 500, "JavaScript": 200},
        blank_lines_by_lang={"Python": 300, "JavaScript": 150},
        lines_by_category={"programming": 7000, "data": 500},
        comment_lines=700,
        blank_lines=450,
        total_lines=7500,
    )


class TestPathTruncation:
    """Tests for path truncation display option."""

    def test_table_formatter_truncates_paths_when_enabled(
        self, sample_metrics: Metrics
    ) -> None:
        """TableFormatter should truncate paths when truncate_paths=True."""
        display_config = DisplayConfig(
            truncate_paths=True,
            show_percentages=True,
        )
        formatter = TableFormatter(display_config)
        result = formatter.format(sample_metrics)

        # Should contain truncated path with ellipsis
        assert "..." in result
        assert "home/user/.../module" in result or "/home/user/.../module" in result

    def test_table_formatter_shows_full_paths_when_disabled(
        self, sample_metrics: Metrics
    ) -> None:
        """TableFormatter should show full paths when truncate_paths=False."""
        display_config = DisplayConfig(
            truncate_paths=False,
            show_percentages=True,
        )
        formatter = TableFormatter(display_config)
        result = formatter.format(sample_metrics)

        # Should contain full path
        assert "/home/user/projects/statsvy/src/module" in result

    def test_markdown_formatter_truncates_paths_when_enabled(
        self, sample_metrics: Metrics
    ) -> None:
        """MarkdownFormatter should truncate paths when truncate_paths=True."""
        display_config = DisplayConfig(
            truncate_paths=True,
            show_percentages=True,
        )
        formatter = MarkdownFormatter(display_config)
        result = formatter.format(sample_metrics)

        # Should contain truncated path
        assert "..." in result
        assert "home/user/.../module" in result or "/home/user/.../module" in result

    def test_markdown_formatter_shows_full_paths_when_disabled(
        self, sample_metrics: Metrics
    ) -> None:
        """MarkdownFormatter should show full paths when truncate_paths=False."""
        display_config = DisplayConfig(
            truncate_paths=False,
            show_percentages=True,
        )
        formatter = MarkdownFormatter(display_config)
        result = formatter.format(sample_metrics)

        # Should contain full path
        assert "/home/user/projects/statsvy/src/module" in result


class TestPercentageDisplay:
    """Tests for percentage column display option."""

    def test_table_formatter_shows_percentages_when_enabled(
        self, sample_metrics: Metrics
    ) -> None:
        """TableFormatter should show percentage columns when show_percentages=True."""
        display_config = DisplayConfig(
            truncate_paths=False,
            show_percentages=True,
        )
        formatter = TableFormatter(display_config)
        result = formatter.format(sample_metrics)

        # Should contain percentage symbol
        assert "%" in result

    def test_table_formatter_hides_percentages_when_disabled(
        self, sample_metrics: Metrics
    ) -> None:
        """TableFormatter should hide percentage columns when show_percentages=False."""
        display_config = DisplayConfig(
            truncate_paths=False,
            show_percentages=False,
        )
        formatter = TableFormatter(display_config)
        result = formatter.format(sample_metrics)

        # Should not contain standalone percentage symbol in tables
        # (Note: Git stats might still have % in some fields)
        lines = result.split("\n")
        category_section = False
        for line in lines:
            if "Lines of Code by" in line:
                category_section = True
            if category_section and ("programming" in line.lower() or "data" in line):
                # These data lines should not have % when disabled
                assert "%" not in line

    def test_markdown_formatter_shows_percentages_when_enabled(
        self, sample_metrics: Metrics
    ) -> None:
        """MarkdownFormatter shows percentage columns when enabled."""
        display_config = DisplayConfig(
            truncate_paths=False,
            show_percentages=True,
        )
        formatter = MarkdownFormatter(display_config)
        result = formatter.format(sample_metrics)

        # Should contain percentage column header and values
        assert "| % |" in result or "|--:|" in result  # Column header or divider

    def test_markdown_formatter_hides_percentages_when_disabled(
        self, sample_metrics: Metrics
    ) -> None:
        """MarkdownFormatter hides percentage columns when disabled."""
        display_config = DisplayConfig(
            truncate_paths=False,
            show_percentages=False,
        )
        formatter = MarkdownFormatter(display_config)
        result = formatter.format(sample_metrics)

        # Check that category table doesn't have % column
        lines = result.split("\n")
        for i, line in enumerate(lines):
            if "## Lines of Code by Type" in line:
                # Next line should be header without %
                header = lines[i + 1]
                assert "| % |" not in header
                break


class TestDefaultBehavior:
    """Tests for default behavior when no display config is provided."""

    def test_table_formatter_defaults_to_full_paths(
        self, sample_metrics: Metrics
    ) -> None:
        """TableFormatter should default to full paths when config is None."""
        formatter = TableFormatter(None)
        result = formatter.format(sample_metrics)

        # Should show full path by default
        assert "/home/user/projects/statsvy/src/module" in result

    def test_table_formatter_defaults_to_showing_percentages(
        self, sample_metrics: Metrics
    ) -> None:
        """TableFormatter should default to showing percentages when config is None."""
        formatter = TableFormatter(None)
        result = formatter.format(sample_metrics)

        # Should show percentages by default
        assert "%" in result

    def test_markdown_formatter_defaults_to_full_paths(
        self, sample_metrics: Metrics
    ) -> None:
        """MarkdownFormatter should default to full paths when config is None."""
        formatter = MarkdownFormatter(None)
        result = formatter.format(sample_metrics)

        # Should show full path by default
        assert "/home/user/projects/statsvy/src/module" in result

    def test_markdown_formatter_defaults_to_showing_percentages(
        self, sample_metrics: Metrics
    ) -> None:
        """MarkdownFormatter defaults to showing percentages."""
        formatter = MarkdownFormatter(None)
        result = formatter.format(sample_metrics)

        # Should show percentages by default
        assert "| % |" in result or "|--:|" in result
