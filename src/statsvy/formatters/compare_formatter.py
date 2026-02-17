"""Formatter module for comparison output between two projects."""

import json
from typing import Any

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from statsvy.data.comparison_result import ComparisonResult
from statsvy.data.config import DisplayConfig
from statsvy.formatters.json_formatter import JsonFormatter
from statsvy.utils.console import console
from statsvy.utils.formatting import delta_str, format_size, percent_delta_str


class CompareFormatter:
    """Formats ComparisonResult objects in various output formats."""

    def __init__(self, display_config: DisplayConfig | None = None) -> None:
        """Initialize formatter with display preferences.

        Args:
            display_config: Optional display configuration overrides.
        """
        self._show_percentages = (
            display_config.show_percentages if display_config else True
        )

    HEADER_COLOR = "bold khaki1"
    LABEL_COLOR = "bold cyan"
    VALUE_COLOR = "bright_white"
    ACCENT_COLOR = "spring_green3"
    BORDER_COLOR = "grey37"

    def format_table(self, comparison: ComparisonResult) -> str:
        """Format comparison as a Rich terminal table.

        Args:
            comparison: The ComparisonResult to display.

        Returns:
            Formatted table output as a string.
        """
        output_parts: list[str] = []

        # Header
        header_text = Text(
            f" Compare: {comparison.project1.name} ↔ {comparison.project2.name} ",
            style=self.HEADER_COLOR,
        )
        header_panel = Panel(
            header_text,
            expand=False,
            border_style=self.HEADER_COLOR,
            box=box.DOUBLE_EDGE,
        )
        with console.capture() as capture:
            console.print(header_panel)
        output_parts.append(capture.get())

        # Overall metrics table
        overall_table = self._create_overall_table(comparison)
        with console.capture() as capture:
            console.print(overall_table)
        output_parts.append(capture.get())

        # By category table
        if (
            comparison.project1.lines_by_category
            or comparison.project2.lines_by_category
        ):
            cat_table = self._create_category_table(comparison)
            with console.capture() as capture:
                console.print(cat_table)
            output_parts.append(capture.get())

        # By language table
        if comparison.project1.lines_by_lang or comparison.project2.lines_by_lang:
            lang_table = self._create_language_table(comparison)
            with console.capture() as capture:
                console.print(lang_table)
            output_parts.append(capture.get())

        return "".join(output_parts)

    def format_json(self, comparison: ComparisonResult) -> str:
        """Format comparison as JSON.

        Args:
            comparison: The ComparisonResult to display.

        Returns:
            Formatted JSON output as a string.
        """
        json_formatter = JsonFormatter()

        data: dict[str, Any] = {
            "project1": json.loads(json_formatter.format(comparison.project1)),
            "project2": json.loads(json_formatter.format(comparison.project2)),
            "comparison": {
                "overall": self._format_deltas_for_json(comparison.deltas["overall"]),
                "by_language": self._format_language_deltas_for_json(
                    comparison.deltas["by_language"]
                ),
                "by_category": self._format_deltas_for_json(
                    comparison.deltas["by_category"]
                ),
            },
        }

        return json.dumps(data, indent=2)

    def format_markdown(self, comparison: ComparisonResult) -> str:
        """Format comparison as Markdown.

        Args:
            comparison: The ComparisonResult to display.

        Returns:
            Formatted Markdown output as a string.
        """
        parts: list[str] = []

        parts.append(
            f"# Comparison: {comparison.project1.name} ↔ {comparison.project2.name}\n"
        )

        # Summary
        parts.append("## Overall Comparison\n")
        parts.append(self._format_overall_markdown(comparison))

        # Category comparison
        if (
            comparison.project1.lines_by_category
            or comparison.project2.lines_by_category
        ):
            parts.append("\n## Lines by Category\n")
            parts.append(self._format_category_markdown(comparison))

        # Language comparison
        if comparison.project1.lines_by_lang or comparison.project2.lines_by_lang:
            parts.append("\n## Lines by Language\n")
            parts.append(self._format_language_markdown(comparison))

        return "\n".join(parts)

    def _add_metric_row(
        self,
        table: Table,
        label: str,
        value1: int | float,
        value2: int | float,
        use_comma: bool = True,
    ) -> None:
        """Add a single metric row to the comparison table.

        Args:
            table: The Rich Table to add the row to.
            label: The metric label/name.
            value1: The value from project1.
            value2: The value from project2.
            use_comma: Whether to use comma formatting for numbers.
        """
        abs_delta = delta_str(value2, value1)
        row_data = [
            label,
            f"{value1:,}" if use_comma and isinstance(value1, int) else str(value1),
            f"{value2:,}" if use_comma and isinstance(value2, int) else str(value2),
            abs_delta,
        ]
        if self._show_percentages:
            pct_delta = percent_delta_str(value2, value1)
            row_data.append(pct_delta)
        table.add_row(*row_data)

    def _create_overall_table(self, comparison: ComparisonResult) -> Table:
        """Create overall metrics comparison table.

        Args:
            comparison: The ComparisonResult object.

        Returns:
            A Rich Table with overall metrics.
        """
        table = Table(
            title="[bold white]Overall Metrics[/bold white]",
            title_justify="left",
            show_header=True,
            header_style=f"bold {self.HEADER_COLOR}",
            border_style=self.BORDER_COLOR,
            box=box.HEAVY_EDGE,
        )

        table.add_column("Metric", style=self.LABEL_COLOR)
        table.add_column(
            comparison.project1.name, justify="right", style=self.VALUE_COLOR
        )
        table.add_column(
            comparison.project2.name, justify="right", style=self.VALUE_COLOR
        )
        table.add_column("Δ (absolute)", justify="right")
        if self._show_percentages:
            table.add_column("Δ (%)", justify="right")

        # Add metric rows
        self._add_metric_row(
            table,
            "Files",
            comparison.project1.total_files,
            comparison.project2.total_files,
        )
        self._add_metric_row(
            table,
            "Total Lines",
            comparison.project1.total_lines,
            comparison.project2.total_lines,
        )

        # Code Lines (calculated)
        p1_code = (
            comparison.project1.total_lines
            - comparison.project1.comment_lines
            - comparison.project1.blank_lines
        )
        p2_code = (
            comparison.project2.total_lines
            - comparison.project2.comment_lines
            - comparison.project2.blank_lines
        )
        self._add_metric_row(table, "Code Lines", p1_code, p2_code)

        self._add_metric_row(
            table,
            "Comment Lines",
            comparison.project1.comment_lines,
            comparison.project2.comment_lines,
        )
        self._add_metric_row(
            table,
            "Blank Lines",
            comparison.project1.blank_lines,
            comparison.project2.blank_lines,
        )

        # Size: display human-readable, deltas from MB values
        self._add_size_row(
            table,
            "Size",
            comparison.project1.total_size_bytes,
            comparison.project2.total_size_bytes,
            comparison.project1.total_size_mb,
            comparison.project2.total_size_mb,
        )

        return table

    def _add_size_row(
        self,
        table: Table,
        label: str,
        p1_bytes: int,
        p2_bytes: int,
        p1_mb: float,
        p2_mb: float,
    ) -> None:
        """Add a size row with human-readable format and deltas.

        Args:
            table: Rich Table to append to.
            label: Display label for the row.
            p1_bytes: Project 1 size in bytes.
            p2_bytes: Project 2 size in bytes.
            p1_mb: Project 1 size in MB (for delta computation).
            p2_mb: Project 2 size in MB (for delta computation).
        """
        abs_delta = delta_str(p2_mb, p1_mb)
        row_data = [
            label,
            format_size(p1_bytes),
            format_size(p2_bytes),
            abs_delta,
        ]
        if self._show_percentages:
            pct_delta = percent_delta_str(p2_mb, p1_mb)
            row_data.append(pct_delta)
        table.add_row(*row_data)

    def _create_category_table(self, comparison: ComparisonResult) -> Table:
        """Create lines-by-category comparison table.

        Args:
            comparison: The ComparisonResult object.

        Returns:
            A Rich Table with category comparisons.
        """
        table = Table(
            title="[bold white]Lines by Category[/bold white]",
            title_justify="left",
            show_header=True,
            header_style=f"bold {self.HEADER_COLOR}",
            border_style=self.BORDER_COLOR,
            box=box.ROUNDED,
        )

        table.add_column("Category", style=self.LABEL_COLOR)
        table.add_column(
            comparison.project1.name, justify="right", style=self.VALUE_COLOR
        )
        table.add_column(
            comparison.project2.name, justify="right", style=self.VALUE_COLOR
        )
        table.add_column("Δ (absolute)", justify="right")
        if self._show_percentages:
            table.add_column("Δ (%)", justify="right")

        all_categories = set(comparison.project1.lines_by_category.keys()) | set(
            comparison.project2.lines_by_category.keys()
        )

        for cat in sorted(all_categories):
            p1_lines = comparison.project1.lines_by_category.get(cat, 0)
            p2_lines = comparison.project2.lines_by_category.get(cat, 0)

            cat_delta = delta_str(p2_lines, p1_lines)
            if self._show_percentages:
                cat_pct = percent_delta_str(p2_lines, p1_lines)
                table.add_row(
                    cat.title(),
                    f"{p1_lines:,}",
                    f"{p2_lines:,}",
                    cat_delta,
                    cat_pct,
                )
            else:
                table.add_row(
                    cat.title(),
                    f"{p1_lines:,}",
                    f"{p2_lines:,}",
                    cat_delta,
                )

        return table

    def _create_language_table(self, comparison: ComparisonResult) -> Table:
        """Create lines-by-language comparison table.

        Args:
            comparison: The ComparisonResult object.

        Returns:
            A Rich Table with language comparisons.
        """
        table = Table(
            title="[bold white]Lines by Language[/bold white]",
            title_justify="left",
            show_header=True,
            header_style=f"bold {self.HEADER_COLOR}",
            border_style=self.BORDER_COLOR,
            box=box.ROUNDED,
        )

        table.add_column("Language", style=self.LABEL_COLOR)
        table.add_column(
            comparison.project1.name, justify="right", style=self.VALUE_COLOR
        )
        table.add_column(
            comparison.project2.name, justify="right", style=self.VALUE_COLOR
        )
        table.add_column("Δ (absolute)", justify="right")
        if self._show_percentages:
            table.add_column("Δ (%)", justify="right")

        all_languages = set(comparison.project1.lines_by_lang.keys()) | set(
            comparison.project2.lines_by_lang.keys()
        )

        for lang in sorted(all_languages):
            p1_lines = comparison.project1.lines_by_lang.get(lang, 0)
            p2_lines = comparison.project2.lines_by_lang.get(lang, 0)

            lang_delta = delta_str(p2_lines, p1_lines)
            if self._show_percentages:
                lang_pct = percent_delta_str(p2_lines, p1_lines)
                table.add_row(
                    lang,
                    f"{p1_lines:,}",
                    f"{p2_lines:,}",
                    lang_delta,
                    lang_pct,
                )
            else:
                table.add_row(
                    lang,
                    f"{p1_lines:,}",
                    f"{p2_lines:,}",
                    lang_delta,
                )

        return table

    def _format_overall_markdown(self, comparison: ComparisonResult) -> str:
        """Format overall comparison as Markdown table.

        Args:
            comparison: The ComparisonResult object.

        Returns:
            Markdown table string for overall metrics.
        """
        p1_code = (
            comparison.project1.total_lines
            - comparison.project1.comment_lines
            - comparison.project1.blank_lines
        )
        p2_code = (
            comparison.project2.total_lines
            - comparison.project2.comment_lines
            - comparison.project2.blank_lines
        )

        def percent_or_zero(absolute: int | float, base: int | float) -> float:
            """Calculate percentage or 0 if base is 0."""
            return (absolute / base * 100) if base > 0 else 0

        # Calculate deltas
        files_delta = comparison.project2.total_files - comparison.project1.total_files
        files_pct = percent_or_zero(files_delta, comparison.project1.total_files)

        lines_delta = comparison.project2.total_lines - comparison.project1.total_lines
        lines_pct = percent_or_zero(lines_delta, comparison.project1.total_lines)

        code_delta = p2_code - p1_code
        code_pct = percent_or_zero(code_delta, p1_code)

        comment_delta = (
            comparison.project2.comment_lines - comparison.project1.comment_lines
        )
        comment_pct = percent_or_zero(comment_delta, comparison.project1.comment_lines)

        blank_delta = comparison.project2.blank_lines - comparison.project1.blank_lines
        blank_pct = percent_or_zero(blank_delta, comparison.project1.blank_lines)

        # Recalculate deltas using bytes for percentage math but show
        # human-readable sizes in the markdown table.
        size_delta_bytes = (
            comparison.project2.total_size_bytes - comparison.project1.total_size_bytes
        )
        size_pct = percent_or_zero(
            size_delta_bytes, comparison.project1.total_size_bytes
        )

        if self._show_percentages:
            lines = [
                "| Metric | Project 1 | Project 2 | Δ (absolute) | Δ (%) |",
                "|--------|----------:|----------:|-------------:|------:|",
                f"| Files | {comparison.project1.total_files:,} | "
                f"{comparison.project2.total_files:,} | {files_delta:+,} | "
                f"{files_pct:+.1f}% |",
                f"| Total Lines | {comparison.project1.total_lines:,} | "
                f"{comparison.project2.total_lines:,} | {lines_delta:+,} | "
                f"{lines_pct:+.1f}% |",
                f"| Code Lines | {p1_code:,} | {p2_code:,} | {code_delta:+,} | "
                f"{code_pct:+.1f}% |",
                f"| Comments | {comparison.project1.comment_lines:,} | "
                f"{comparison.project2.comment_lines:,} | {comment_delta:+,} | "
                f"{comment_pct:+.1f}% |",
                f"| Blank Lines | {comparison.project1.blank_lines:,} | "
                f"{comparison.project2.blank_lines:,} | {blank_delta:+,} | "
                f"{blank_pct:+.1f}% |",
                f"| Size | {format_size(comparison.project1.total_size_bytes)} | "
                f"{format_size(comparison.project2.total_size_bytes)} | "
                f"{size_delta_bytes:+} | "
                f"{size_pct:+.1f}% |",
            ]
        else:
            lines = [
                "| Metric | Project 1 | Project 2 | Δ (absolute) |",
                "|--------|----------:|----------:|-------------:|",
                f"| Files | {comparison.project1.total_files:,} | "
                f"{comparison.project2.total_files:,} | {files_delta:+,} |",
                f"| Total Lines | {comparison.project1.total_lines:,} | "
                f"{comparison.project2.total_lines:,} | {lines_delta:+,} |",
                f"| Code Lines | {p1_code:,} | {p2_code:,} | {code_delta:+,} |",
                f"| Comments | {comparison.project1.comment_lines:,} | "
                f"{comparison.project2.comment_lines:,} | {comment_delta:+,} |",
                f"| Blank Lines | {comparison.project1.blank_lines:,} | "
                f"{comparison.project2.blank_lines:,} | {blank_delta:+,} |",
                f"| Size | {format_size(comparison.project1.total_size_bytes)} | "
                f"{format_size(comparison.project2.total_size_bytes)} | "
                f"{size_delta_bytes:+} |",
            ]

        return "\n".join(lines)

    def _format_category_markdown(self, comparison: ComparisonResult) -> str:
        """Format category comparison as Markdown table.

        Args:
            comparison: The ComparisonResult object.

        Returns:
            Markdown table string for category metrics.
        """
        all_categories = set(comparison.project1.lines_by_category.keys()) | set(
            comparison.project2.lines_by_category.keys()
        )

        if self._show_percentages:
            lines = [
                "| Category | Project 1 | Project 2 | Δ (absolute) | Δ (%) |",
                "|----------|----------:|----------:|-------------:|------:|",
            ]
        else:
            lines = [
                "| Category | Project 1 | Project 2 | Δ (absolute) |",
                "|----------|----------:|----------:|-------------:|",
            ]

        for cat in sorted(all_categories):
            p1_lines = comparison.project1.lines_by_category.get(cat, 0)
            p2_lines = comparison.project2.lines_by_category.get(cat, 0)
            if self._show_percentages:
                pct_change = (
                    ((p2_lines - p1_lines) / p1_lines * 100) if p1_lines > 0 else 0
                )
                lines.append(
                    f"| {cat.title()} | {p1_lines:,} | {p2_lines:,} | "
                    f"{p2_lines - p1_lines:+,} | {pct_change:+.1f}% |"
                )
            else:
                lines.append(
                    f"| {cat.title()} | {p1_lines:,} | {p2_lines:,} | "
                    f"{p2_lines - p1_lines:+,} |"
                )

        return "\n".join(lines)

    def _format_language_markdown(self, comparison: ComparisonResult) -> str:
        """Format language comparison as Markdown table.

        Args:
            comparison: The ComparisonResult object.

        Returns:
            Markdown table string for language metrics.
        """
        all_languages = set(comparison.project1.lines_by_lang.keys()) | set(
            comparison.project2.lines_by_lang.keys()
        )

        if self._show_percentages:
            lines = [
                "| Language | Project 1 | Project 2 | Δ (absolute) | Δ (%) |",
                "|----------|----------:|----------:|-------------:|------:|",
            ]
        else:
            lines = [
                "| Language | Project 1 | Project 2 | Δ (absolute) |",
                "|----------|----------:|----------:|-------------:|",
            ]

        for lang in sorted(all_languages):
            p1_lines = comparison.project1.lines_by_lang.get(lang, 0)
            p2_lines = comparison.project2.lines_by_lang.get(lang, 0)
            if self._show_percentages:
                pct_change = (
                    ((p2_lines - p1_lines) / p1_lines * 100) if p1_lines > 0 else 0
                )
                lines.append(
                    f"| {lang} | {p1_lines:,} | {p2_lines:,} | "
                    f"{p2_lines - p1_lines:+,} | {pct_change:+.1f}% |"
                )
            else:
                lines.append(
                    f"| {lang} | {p1_lines:,} | {p2_lines:,} | "
                    f"{p2_lines - p1_lines:+,} |"
                )

        return "\n".join(lines)

    def _format_deltas_for_json(self, deltas: dict[str, Any]) -> dict[str, Any]:
        """Convert deltas to JSON-serializable format.

        Args:
            deltas: Dictionary of deltas.

        Returns:
            Same dictionary (already JSON-serializable).
        """
        return deltas

    def _format_language_deltas_for_json(
        self, lang_deltas: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Convert language deltas to JSON-serializable format.

        Args:
            lang_deltas: Dictionary of language deltas.

        Returns:
            Same dictionary (already JSON-serializable).
        """
        return lang_deltas
