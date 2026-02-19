"""Tests for ComparisonAnalyzer."""

from statsvy.core.comparison import ComparisonAnalyzer
from statsvy.data.comparison_result import ComparisonResult
from statsvy.data.metrics import Metrics


class TestComparisonAnalyzer:
    """Tests for ComparisonAnalyzer behaviour and delta calculations."""

    def test_comparison_analyzer_returns_comparison_result(
        self, sample_metrics_project1: Metrics, sample_metrics_project2: Metrics
    ) -> None:
        """ComparisonAnalyzer.compare() should return a ComparisonResult."""
        result = ComparisonAnalyzer.compare(
            sample_metrics_project1, sample_metrics_project2
        )

        assert isinstance(result, ComparisonResult)
        assert result.project1 == sample_metrics_project1
        assert result.project2 == sample_metrics_project2
        assert result.deltas is not None

    def test_comparison_overall_metrics_deltas(
        self, sample_metrics_project1: Metrics, sample_metrics_project2: Metrics
    ) -> None:
        """Overall metrics should show correct absolute deltas."""
        result = ComparisonAnalyzer.compare(
            sample_metrics_project1, sample_metrics_project2
        )
        overall_deltas = result.deltas["overall"]

        assert overall_deltas["total_files"] == 58 - 42  # +16
        assert overall_deltas["total_lines"] == 5670 - 4000  # +1670
        assert overall_deltas["total_size_bytes"] == 2097152 - 1048576
        assert overall_deltas["total_size_mb"] == 2 - 1  # +1
        assert overall_deltas["comment_lines"] == 910 - 650  # +260
        assert overall_deltas["blank_lines"] == 660 - 450  # +210

    def test_comparison_language_deltas_all_languages_included(
        self, sample_metrics_project1: Metrics, sample_metrics_project2: Metrics
    ) -> None:
        """All languages from both projects should be in deltas (including Go)."""
        result = ComparisonAnalyzer.compare(
            sample_metrics_project1, sample_metrics_project2
        )
        lang_deltas = result.deltas["by_language"]

        assert "Python" in lang_deltas
        assert "JavaScript" in lang_deltas
        assert "TypeScript" in lang_deltas
        assert "Go" in lang_deltas

    def test_comparison_language_deltas_python(
        self, sample_metrics_project1: Metrics, sample_metrics_project2: Metrics
    ) -> None:
        """Python should show correct deltas."""
        result = ComparisonAnalyzer.compare(
            sample_metrics_project1, sample_metrics_project2
        )
        py_deltas = result.deltas["by_language"]["Python"]

        assert py_deltas["lines"] == 3200 - 2500  # +700
        assert py_deltas["comments"] == 650 - 500  # +150
        assert py_deltas["blank"] == 400 - 300  # +100

    def test_comparison_language_new_in_project2(
        self, sample_metrics_project1: Metrics, sample_metrics_project2: Metrics
    ) -> None:
        """Go language (only in project2) should have None deltas."""
        result = ComparisonAnalyzer.compare(
            sample_metrics_project1, sample_metrics_project2
        )
        go_deltas = result.deltas["by_language"]["Go"]

        # project1 has no Go, so deltas are None
        assert go_deltas["lines"] is None
        assert go_deltas["comments"] is None
        assert go_deltas["blank"] is None

    def test_comparison_category_deltas(
        self, sample_metrics_project1: Metrics, sample_metrics_project2: Metrics
    ) -> None:
        """Category deltas should be correct."""
        result = ComparisonAnalyzer.compare(
            sample_metrics_project1, sample_metrics_project2
        )
        cat_deltas = result.deltas["by_category"]

        assert cat_deltas["code"] == 4100 - 2700  # +1400
        assert cat_deltas["comment"] == 910 - 650  # +260
        assert cat_deltas["blank"] == 660 - 450  # +210

    def test_comparison_with_identical_metrics(
        self,
        sample_metrics_project1: Metrics,
    ) -> None:
        """Comparing identical metrics should show zero deltas."""
        result = ComparisonAnalyzer.compare(
            sample_metrics_project1, sample_metrics_project1
        )
        overall_deltas = result.deltas["overall"]

        assert overall_deltas["total_files"] == 0
        assert overall_deltas["total_lines"] == 0
        assert overall_deltas["total_size_bytes"] == 0

    def test_comparison_with_smaller_project(
        self, sample_metrics_project1: Metrics, sample_metrics_project2: Metrics
    ) -> None:
        """Comparing smaller project second should show negative deltas."""
        result = ComparisonAnalyzer.compare(
            sample_metrics_project2, sample_metrics_project1
        )
        overall_deltas = result.deltas["overall"]

        assert overall_deltas["total_files"] == 42 - 58  # -16
        assert overall_deltas["total_lines"] == 4000 - 5670  # -1670
