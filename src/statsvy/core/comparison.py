"""Analysis of metrics from two different projects for comparison.

This module provides functionality to compute deltas and comparisons
between two Metrics snapshots from different projects.
"""

import datetime
from typing import Any

from statsvy.data.comparison_result import ComparisonResult
from statsvy.data.metrics import Metrics


class ComparisonAnalyzer:
    """Analyzes and compares two Metrics objects.

    Computes absolute and relative deltas for all metrics, handling cases
    where metrics may not exist in one or both projects (e.g., languages
    only in one project, or missing git information).
    """

    @staticmethod
    def compare(
        project1_metrics: Metrics, project2_metrics: Metrics
    ) -> ComparisonResult:
        """Compare two project metrics and compute all deltas.

        Args:
            project1_metrics: Metrics from the first project.
            project2_metrics: Metrics from the second project.

        Returns:
            ComparisonResult containing both metrics and computed deltas.
        """
        deltas = ComparisonAnalyzer._compute_deltas(project1_metrics, project2_metrics)

        return ComparisonResult(
            project1=project1_metrics,
            project2=project2_metrics,
            deltas=deltas,
            timestamp=datetime.datetime.now(),
        )

    @staticmethod
    def _compute_deltas(project1: Metrics, project2: Metrics) -> dict[str, Any]:
        """Compute all metric deltas between two projects.

        Organizes deltas by category: 'overall', 'by_language', 'by_category'.

        Args:
            project1: First project's metrics.
            project2: Second project's metrics.

        Returns:
            Dict of delta categories to their metric deltas.
        """
        deltas: dict[str, Any] = {}

        # Overall metrics deltas
        deltas["overall"] = ComparisonAnalyzer._delta_overall(project1, project2)

        # By-language deltas (all languages from both projects)
        deltas["by_language"] = ComparisonAnalyzer._delta_by_language(
            project1, project2
        )

        # By-category deltas (code, comment, blank)
        deltas["by_category"] = ComparisonAnalyzer._delta_by_category(
            project1, project2
        )

        return deltas

    @staticmethod
    def _delta_overall(project1: Metrics, project2: Metrics) -> dict[str, int]:
        """Compute deltas for overall metrics.

        Args:
            project1: First project's metrics.
            project2: Second project's metrics.

        Returns:
            Mapping of metric names to their absolute deltas.
        """
        return {
            "total_files": project2.total_files - project1.total_files,
            "total_lines": project2.total_lines - project1.total_lines,
            "total_size_bytes": project2.total_size_bytes - project1.total_size_bytes,
            "total_size_kb": project2.total_size_kb - project1.total_size_kb,
            "total_size_mb": project2.total_size_mb - project1.total_size_mb,
            "comment_lines": project2.comment_lines - project1.comment_lines,
            "blank_lines": project2.blank_lines - project1.blank_lines,
        }

    @staticmethod
    def _delta_by_language(
        project1: Metrics, project2: Metrics
    ) -> dict[str, dict[str, int | None]]:
        """Compute deltas for all languages (from both projects).

        Handles languages present in only one project by using None
        as a sentinel value.

        Args:
            project1: First project's metrics.
            project2: Second project's metrics.

        Returns:
            Mapping of language names to their deltas.
        """
        all_languages = set(project1.lines_by_lang.keys()) | set(
            project2.lines_by_lang.keys()
        )

        language_deltas: dict[str, dict[str, int | None]] = {}

        for lang in sorted(all_languages):
            p1_lines = project1.lines_by_lang.get(lang)
            p2_lines = project2.lines_by_lang.get(lang)

            delta_lines = (
                (p2_lines - p1_lines)
                if p1_lines is not None and p2_lines is not None
                else None
            )

            p1_comments = project1.comment_lines_by_lang.get(lang)
            p2_comments = project2.comment_lines_by_lang.get(lang)

            delta_comments = (
                (p2_comments - p1_comments)
                if p1_comments is not None and p2_comments is not None
                else None
            )

            p1_blank = project1.blank_lines_by_lang.get(lang)
            p2_blank = project2.blank_lines_by_lang.get(lang)

            delta_blank = (
                (p2_blank - p1_blank)
                if p1_blank is not None and p2_blank is not None
                else None
            )

            language_deltas[lang] = {
                "lines": delta_lines,
                "comments": delta_comments,
                "blank": delta_blank,
            }

        return language_deltas

    @staticmethod
    def _delta_by_category(
        project1: Metrics, project2: Metrics
    ) -> dict[str, int | None]:
        """Compute deltas for line categories (code, comment, blank).

        Args:
            project1: First project's metrics.
            project2: Second project's metrics.

        Returns:
            Mapping of category names to their deltas.
        """
        all_categories = set(project1.lines_by_category.keys()) | set(
            project2.lines_by_category.keys()
        )

        category_deltas: dict[str, int | None] = {}

        for cat in sorted(all_categories):
            p1_lines = project1.lines_by_category.get(cat)
            p2_lines = project2.lines_by_category.get(cat)

            delta = (
                (p2_lines - p1_lines)
                if p1_lines is not None and p2_lines is not None
                else None
            )

            category_deltas[cat] = delta

        return category_deltas
