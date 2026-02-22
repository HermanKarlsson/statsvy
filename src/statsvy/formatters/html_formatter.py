"""Formatter module for simple HTML output.

This formatter previously produced entirely unstyled documents; a small
embedded stylesheet can now be included by default, and it may be disabled
via `include_css=False` (e.g. when the `--no-css` CLI flag is used).
"""

from html import escape

from statsvy.data.config import DisplayConfig, GitConfig
from statsvy.data.git_info import GitInfo
from statsvy.data.metrics import Metrics
from statsvy.data.project_info import DependencyInfo
from statsvy.utils.formatting import format_size, truncate_path_display


class HtmlFormatter:
    """Formats Metrics objects as basic HTML strings.

    The output is intentionally minimal: a full HTML document with an optional
    embedded stylesheet (disabled by default via ``include_css=False``). Tables
    are used for summary, category and language sections. This formatter is
    intended to be consumed by a browser or saved to a file.
    """

    def __init__(
        self,
        display_config: DisplayConfig | None = None,
        git_config: GitConfig | None = None,
        include_css: bool = True,
    ) -> None:
        """Initialize formatter with display preferences.

        Args:
            display_config: Optional display configuration overrides.
            git_config: Optional git configuration settings.
            include_css: Whether to include a small embedded stylesheet in
                the generated HTML. This can be disabled via the CLI
                "--no-css" flag.
        """
        self._truncate_paths = (
            display_config.truncate_paths if display_config else False
        )
        self._show_percentages = (
            display_config.show_percentages if display_config else True
        )
        # dependency section should behave like other formatters
        self._show_deps_list = display_config.show_deps_list if display_config else True
        self._show_contributors = git_config.show_contributors if git_config else True
        self._include_css = include_css

    def format(self, metrics: Metrics, git_info: GitInfo | None = None) -> str:
        """Format metrics data as a simple HTML document.

        Args:
            metrics: The Metrics object to format.
            git_info: Optional Git repository metadata to include.

        Returns:
            str: An HTML document representing the metrics.
        """
        # start document
        title = escape(metrics.name)
        html_parts: list[str] = [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            f'<meta charset="utf-8"/><title>{title}</title>',
        ]
        if self._include_css:
            # simple CSS to make tables readable without external dependencies
            html_parts.append(
                "<style>"
                "body{font-family:Arial,Helvetica,sans-serif;margin:1em;}"
                "table{border-collapse:collapse;width:100%;}"
                "th,td{border:1px solid #ccc;padding:0.5em;text-align:left;}"
                "h1,h2,h3{color:#333;}"
                "</style>"
            )
        html_parts.append("</head>")
        html_parts.append("<body>")
        html_parts.append(f"<h1>Scan: {title}</h1>")

        html_parts.append(self._format_summary(metrics, git_info))

        if hasattr(metrics, "lines_by_category") and metrics.lines_by_category:
            html_parts.append(self._format_category_table(metrics))

        if metrics.lines_by_lang:
            html_parts.append(self._format_language_table(metrics))

        deps = getattr(metrics, "dependencies", None)
        if deps is not None:
            # mypy can't narrow the type of an attribute, so store locally
            assert deps is not None
            html_parts.append(self._format_dependencies(deps))

        html_parts.append("</body>")
        html_parts.append("</html>")

        return "\n".join(html_parts)

    def _format_summary(self, metrics: Metrics, git_info: GitInfo | None) -> str:
        """Return HTML for summary information."""
        path_value = (
            truncate_path_display(metrics.path)
            if self._truncate_paths
            else str(metrics.path)
        )

        bytes_val: int | None = None
        tsb = getattr(metrics, "total_size_bytes", None)
        if isinstance(tsb, int | float):
            bytes_val = int(tsb)
        else:
            tsk = getattr(metrics, "total_size_kb", None)
            if isinstance(tsk, int | float):
                bytes_val = int(tsk) * 1024
            else:
                tsm = getattr(metrics, "total_size_mb", None)
                if isinstance(tsm, int | float):
                    bytes_val = int(tsm * 1024 * 1024)

        lines: list[str] = [
            "<h2>Project Statistics</h2>",
            "<table>",
            "<tr><th>Field</th><th>Value</th></tr>",
            f"<tr><td>Path</td><td>{escape(path_value)}</td></tr>",
            f"<tr><td>Timestamp</td><td>{escape(metrics.timestamp.strftime('%Y-%m-%d'))}</td></tr>",
            f"<tr><td>Files</td><td>{metrics.total_files:,}</td></tr>",
            f"<tr><td>Size</td><td>{escape(format_size(bytes_val or 0))}</td></tr>",
            f"<tr><td>Total Lines</td><td>{metrics.total_lines:,}</td></tr>",
        ]

        if git_info is not None:
            repo_label = "Yes" if git_info.is_git_repo else "No"
            contributors = (
                ", ".join(git_info.contributors) if git_info.contributors else "-"
            )
            lines.extend(
                [
                    f"<tr><td>Git Repo</td><td>{repo_label}</td></tr>",
                    f"<tr><td>Git Branch</td><td>{escape(git_info.current_branch or '-')}</td></tr>",  # noqa: E501
                    f"<tr><td>Git Remote</td><td>{escape(git_info.remote_url or '-')}</td></tr>",  # noqa: E501
                ]
            )
            if self._show_contributors:
                lines.append(
                    f"<tr><td>Contributors</td><td>{escape(contributors)}</td></tr>"
                )
            # other git info omitted for MVP
        lines.append("</table>")
        return "\n".join(lines)

    def _format_category_table(self, metrics: Metrics) -> str:
        """Return HTML table for lines-by-category."""
        rows: list[str] = []
        for category, count in sorted(
            metrics.lines_by_category.items(), key=lambda x: x[1], reverse=True
        ):
            display_name = category.title() if category != "unknown" else "Unknown"
            if self._show_percentages:
                pct = (
                    (count / metrics.total_lines * 100)
                    if metrics.total_lines > 0
                    else 0
                )
                rows.append(
                    f"<tr><td>{escape(display_name)}</td><td>{count:,}</td><td>{pct:.1f}%</td></tr>"
                )
            else:
                rows.append(
                    f"<tr><td>{escape(display_name)}</td><td>{count:,}</td></tr>"
                )
        header = (
            "<tr><th>Category</th><th>Lines</th><th>%</th></tr>"
            if self._show_percentages
            else "<tr><th>Category</th><th>Lines</th></tr>"
        )
        table = ["<h2>Lines of Code by Type</h2>", "<table>", header]
        table.extend(rows)
        table.append("</table>")
        return "\n".join(table)

    def _format_language_table(self, metrics: Metrics) -> str:
        """Return HTML table for lines-by-language."""
        header_cells = ["Language", "Lines"]
        if self._show_percentages:
            header_cells.append("%")
        header_cells.extend(["Code", "Comments", "Blank"])
        header = "".join(f"<th>{cell}</th>" for cell in header_cells)
        rows: list[str] = []
        for lang, lines_count in sorted(
            metrics.lines_by_lang.items(), key=lambda x: x[1], reverse=True
        ):
            comments = metrics.comment_lines_by_lang.get(lang, 0)
            blanks = metrics.blank_lines_by_lang.get(lang, 0)
            code = lines_count - comments - blanks
            cells = [escape(lang), f"{lines_count:,}"]
            if self._show_percentages:
                pct = (
                    (lines_count / metrics.total_lines * 100)
                    if metrics.total_lines > 0
                    else 0
                )
                cells.append(f"{pct:.1f}%")
            cells.extend([f"{code:,}", f"{comments:,}", f"{blanks:,}"])
            rows.append("".join(f"<td>{c}</td>" for c in cells))
        table = ["<h2>Lines of Code by Language</h2>", "<table>", f"<tr>{header}</tr>"]
        for r in rows:
            table.append(f"<tr>{r}</tr>")
        table.append("</table>")
        return "\n".join(table)

    # dependency formatting ------------------------------------------------
    def _format_dependencies(self, dep_info: DependencyInfo) -> str:
        """Return HTML representation of dependency statistics.

        The structure mirrors the Markdown formatter but uses HTML tables and
        lists. It respects ``self._show_deps_list`` to optionally render the
        per-package table.
        """
        parts: list[str] = []
        parts.append("<h2>Dependencies</h2>")
        parts.append("<table>")
        parts.append("<tr><th>Category</th><th>Count</th></tr>")
        parts.append(f"<tr><td>Production</td><td>{dep_info.prod_count}</td></tr>")
        parts.append(f"<tr><td>Development</td><td>{dep_info.dev_count}</td></tr>")
        parts.append(f"<tr><td>Optional</td><td>{dep_info.optional_count}</td></tr>")
        parts.append(
            f"<tr><td><strong>Total</strong></td><td><strong>{dep_info.total_count}</strong></td></tr>"
        )
        parts.append("</table>")

        if dep_info.sources:
            parts.append(f"<p>Sources: {escape(', '.join(dep_info.sources))}</p>")

        if dep_info.conflicts:
            parts.append("<h3>Conflicts</h3>")
            parts.append("<ul>")
            for c in dep_info.conflicts:
                parts.append(f"<li>{escape(c)}</li>")
            parts.append("</ul>")

        if self._show_deps_list and dep_info.dependencies:
            _cat_order = {"prod": 0, "dev": 1, "optional": 2}
            _cat_label = {
                "prod": "Production",
                "dev": "Development",
                "optional": "Optional",
            }
            sorted_deps = sorted(
                dep_info.dependencies,
                key=lambda d: (_cat_order.get(d.category, 99), d.name.lower()),
            )
            parts.append("<h3>Packages</h3>")
            parts.append("<table>")
            parts.append("<tr><th>Name</th><th>Version</th><th>Category</th></tr>")
            for d in sorted_deps:
                label = _cat_label.get(d.category, d.category.title())
                version = d.version or "-"
                parts.append(
                    f"<tr><td>{escape(d.name)}</td><td>{escape(version)}</td><td>{escape(label)}</td></tr>"
                )
            parts.append("</table>")

        return "\n".join(parts)
