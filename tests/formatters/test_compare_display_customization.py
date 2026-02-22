"""Tests for CompareFormatter display customization."""

from datetime import datetime
from pathlib import Path

import pytest

from statsvy.core.comparison import ComparisonAnalyzer
from statsvy.core.formatter import Formatter
from statsvy.data.config import DisplayConfig
from statsvy.data.metrics import Metrics
from statsvy.formatters.compare_formatter import CompareFormatter


@pytest.fixture
def project1_metrics() -> Metrics:
    """Create first project metrics for comparison testing."""
    return Metrics(
        name="Project Alpha",
        path=Path("/home/user/project1"),
        timestamp=datetime(2024, 1, 1, 10, 0, 0),
        total_files=100,
        total_size_bytes=2097152,
        total_size_kb=2048,
        total_size_mb=2,
        lines_by_lang={"Python": 5000, "JavaScript": 2000},
        comment_lines_by_lang={"Python": 500, "JavaScript": 200},
        blank_lines_by_lang={"Python": 300, "JavaScript": 150},
        lines_by_category={"programming": 7000},
        comment_lines=700,
        blank_lines=450,
        total_lines=7500,
    )


@pytest.fixture
def project2_metrics() -> Metrics:
    """Create second project metrics for comparison testing."""
    return Metrics(
        name="Project Beta",
        path=Path("/home/user/project2"),
        timestamp=datetime(2024, 2, 1, 10, 0, 0),
        total_files=120,
        total_size_bytes=2621440,
        total_size_kb=2560,
        total_size_mb=3,
        lines_by_lang={"Python": 6000, "JavaScript": 2500},
        comment_lines_by_lang={"Python": 600, "JavaScript": 250},
        blank_lines_by_lang={"Python": 350, "JavaScript": 180},
        lines_by_category={"programming": 8500},
        comment_lines=850,
        blank_lines=530,
        total_lines=9000,
    )


class TestCompareFormatterPercentages:
    """Tests for percentage display in comparison formatter."""

    def test_table_format_shows_percentages_when_enabled(
        self, project1_metrics: Metrics, project2_metrics: Metrics
    ) -> None:
        """CompareFormatter table should show percentage deltas when enabled."""
        comparison = ComparisonAnalyzer.compare(project1_metrics, project2_metrics)
        display_config = DisplayConfig(truncate_paths=False, show_percentages=True)
        formatter = CompareFormatter(display_config)
        result = formatter.format_table(comparison)

        # Should contain percentage delta column
        assert "Δ (%)" in result or "%" in result

    def test_table_format_hides_percentages_when_disabled(
        self, project1_metrics: Metrics, project2_metrics: Metrics
    ) -> None:
        """CompareFormatter table should hide percentage deltas when disabled."""
        comparison = ComparisonAnalyzer.compare(project1_metrics, project2_metrics)
        display_config = DisplayConfig(truncate_paths=False, show_percentages=False)
        formatter = CompareFormatter(display_config)
        result = formatter.format_table(comparison)

        # Should contain absolute delta but not percentage delta column
        assert "Δ (absolute)" in result
        # Check that we don't have a dedicated percentage column header
        lines = result.split("\n")
        for line in lines:
            is_header_line = (
                ("Overall Metrics" in line or "Lines by" in line)
                and "|" in line
                and "Metric" in line
            )
            if is_header_line:
                # Table headers should not have Δ (%) when disabled
                assert "Δ (%)" not in line

    def test_markdown_format_shows_percentages_when_enabled(
        self, project1_metrics: Metrics, project2_metrics: Metrics
    ) -> None:
        """CompareFormatter markdown should show percentage deltas when enabled."""
        comparison = ComparisonAnalyzer.compare(project1_metrics, project2_metrics)
        display_config = DisplayConfig(truncate_paths=False, show_percentages=True)
        formatter = CompareFormatter(display_config)
        result = formatter.format_markdown(comparison)

        # Should contain percentage column in markdown tables
        assert "| Δ (%) |" in result

    def test_markdown_format_hides_percentages_when_disabled(
        self, project1_metrics: Metrics, project2_metrics: Metrics
    ) -> None:
        """CompareFormatter markdown should hide percentage deltas when disabled."""
        comparison = ComparisonAnalyzer.compare(project1_metrics, project2_metrics)
        display_config = DisplayConfig(truncate_paths=False, show_percentages=False)
        formatter = CompareFormatter(display_config)
        result = formatter.format_markdown(comparison)

        # Should not contain percentage column
        assert "| Δ (%) |" not in result
        # Should still have absolute delta
        assert "| Δ (absolute) |" in result

    def test_default_shows_percentages(
        self, project1_metrics: Metrics, project2_metrics: Metrics
    ) -> None:
        """CompareFormatter should default to showing percentages."""
        comparison = ComparisonAnalyzer.compare(project1_metrics, project2_metrics)
        formatter = CompareFormatter(None)
        result = formatter.format_table(comparison)

        # Default should show percentages
        assert "%" in result

    # HTML-specific tests using the central Formatter to exercise include_css
    def test_comparison_html_includes_css(
        self, project1_metrics: Metrics, project2_metrics: Metrics
    ) -> None:
        """When HTML is requested without disabling CSS a <style> tag appears."""
        comparison = ComparisonAnalyzer.compare(project1_metrics, project2_metrics)
        html = Formatter.format(
            comparison,
            "html",
            display_config=DisplayConfig(truncate_paths=False, show_percentages=True),
            include_css=True,
        )
        assert html.strip().startswith("<!DOCTYPE html>")
        assert "<style" in html

    def test_comparison_html_no_css(
        self, project1_metrics: Metrics, project2_metrics: Metrics
    ) -> None:
        """Setting include_css=False should omit any <style> block."""
        comparison = ComparisonAnalyzer.compare(project1_metrics, project2_metrics)
        html = Formatter.format(
            comparison,
            "html",
            display_config=DisplayConfig(truncate_paths=False, show_percentages=True),
            include_css=False,
        )
        assert html.strip().startswith("<!DOCTYPE html>")
        assert "<style" not in html
