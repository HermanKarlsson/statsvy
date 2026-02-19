"""Tests for CompareFormatter."""

import json

from statsvy.core.comparison import ComparisonAnalyzer
from statsvy.data.metrics import Metrics
from statsvy.formatters.compare_formatter import CompareFormatter


def test_compare_formatter_table_contains_project_names(
    sample_metrics_project1: Metrics, sample_metrics_project2: Metrics
) -> None:
    """Table output should contain both project names."""
    comparison = ComparisonAnalyzer.compare(
        sample_metrics_project1, sample_metrics_project2
    )
    formatter = CompareFormatter()
    output = formatter.format_table(comparison)

    assert sample_metrics_project1.name in output
    assert sample_metrics_project2.name in output


def test_compare_formatter_table_contains_metrics(
    sample_metrics_project1: Metrics, sample_metrics_project2: Metrics
) -> None:
    """Table output should contain metric values."""
    comparison = ComparisonAnalyzer.compare(
        sample_metrics_project1, sample_metrics_project2
    )
    formatter = CompareFormatter()
    output = formatter.format_table(comparison)

    # Should contain file counts
    assert "42" in output  # project1 files
    assert "58" in output  # project2 files

    # Should contain line counts (Rich adds commas for thousands)
    assert "4,000" in output  # project1 lines
    assert "5,670" in output  # project2 lines


def test_compare_formatter_table_contains_deltas(
    sample_metrics_project1: Metrics, sample_metrics_project2: Metrics
) -> None:
    """Table output should contain delta information."""
    comparison = ComparisonAnalyzer.compare(
        sample_metrics_project1, sample_metrics_project2
    )
    formatter = CompareFormatter()
    output = formatter.format_table(comparison)

    # Should show deltas (may be formatted with +/- and colors)
    assert "16" in output or "+16" in output  # file delta
    # Rich adds commas for thousands
    assert "1,670" in output or "+1,670" in output  # line delta


def test_compare_formatter_json_valid(
    sample_metrics_project1: Metrics, sample_metrics_project2: Metrics
) -> None:
    """JSON output should be valid JSON."""
    comparison = ComparisonAnalyzer.compare(
        sample_metrics_project1, sample_metrics_project2
    )
    formatter = CompareFormatter()
    output = formatter.format_json(comparison)

    # Should parse as valid JSON
    data = json.loads(output)
    assert "project1" in data
    assert "project2" in data
    assert "comparison" in data


def test_compare_formatter_json_contains_projects(
    sample_metrics_project1: Metrics, sample_metrics_project2: Metrics
) -> None:
    """JSON should contain both project metrics."""
    comparison = ComparisonAnalyzer.compare(
        sample_metrics_project1, sample_metrics_project2
    )
    formatter = CompareFormatter()
    output = formatter.format_json(comparison)
    data = json.loads(output)

    assert data["project1"]["name"] == "Project Alpha"
    assert data["project2"]["name"] == "Project Beta"


def test_compare_formatter_json_contains_comparison(
    sample_metrics_project1: Metrics, sample_metrics_project2: Metrics
) -> None:
    """JSON should contain comparison deltas."""
    comparison = ComparisonAnalyzer.compare(
        sample_metrics_project1, sample_metrics_project2
    )
    formatter = CompareFormatter()
    output = formatter.format_json(comparison)
    data = json.loads(output)

    assert "overall" in data["comparison"]
    assert "by_language" in data["comparison"]
    assert "by_category" in data["comparison"]

    # Check some deltas
    assert data["comparison"]["overall"]["total_files"] == 16


def test_compare_formatter_markdown_contains_headers(
    sample_metrics_project1: Metrics, sample_metrics_project2: Metrics
) -> None:
    """Markdown output should contain section headers."""
    comparison = ComparisonAnalyzer.compare(
        sample_metrics_project1, sample_metrics_project2
    )
    formatter = CompareFormatter()
    output = formatter.format_markdown(comparison)

    assert "# Comparison" in output
    assert "## Overall Comparison" in output
    assert "## Lines by Category" in output
    assert "## Lines by Language" in output


def test_compare_formatter_markdown_contains_tables(
    sample_metrics_project1: Metrics, sample_metrics_project2: Metrics
) -> None:
    """Markdown output should contain markdown tables."""
    comparison = ComparisonAnalyzer.compare(
        sample_metrics_project1, sample_metrics_project2
    )
    formatter = CompareFormatter()
    output = formatter.format_markdown(comparison)

    # Check for markdown table syntax
    assert "|" in output
    assert "---" in output


def test_compare_formatter_markdown_contains_values(
    sample_metrics_project1: Metrics, sample_metrics_project2: Metrics
) -> None:
    """Markdown output should contain metric values."""
    comparison = ComparisonAnalyzer.compare(
        sample_metrics_project1, sample_metrics_project2
    )
    formatter = CompareFormatter()
    output = formatter.format_markdown(comparison)

    # Check for project names
    assert "Project Alpha" in output
    assert "Project Beta" in output

    # Check for some values
    assert "42" in output  # files from project1
    assert "58" in output  # files from project2
