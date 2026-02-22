"""Coordinator module for displaying metrics in various formats."""

from html import escape

from statsvy.data.comparison_result import ComparisonResult
from statsvy.data.config import DisplayConfig, GitConfig
from statsvy.data.git_info import GitInfo
from statsvy.data.metrics import Metrics
from statsvy.formatters.compare_formatter import CompareFormatter
from statsvy.formatters.html_formatter import HtmlFormatter
from statsvy.formatters.json_formatter import JsonFormatter
from statsvy.formatters.markdown_formatter import MarkdownFormatter
from statsvy.formatters.table_formatter import TableFormatter


class Formatter:
    """Coordinator that delegates formatting to specific implementations."""

    @staticmethod
    def format(
        data: Metrics | ComparisonResult,
        format_type: str | None = "table",
        git_info: GitInfo | None = None,
        display_config: DisplayConfig | None = None,
        git_config: GitConfig | None = None,
        include_css: bool | None = None,
    ) -> str:
        """Format metrics or comparison data based on the requested format type.

        Args:
            data: The Metrics or ComparisonResult object to display.
            format_type: The format identifier (e.g., 'table', 'json', 'md').
            git_info: Optional Git repository metadata to include
                (ignored for comparisons).
            display_config: Display customization options for paths and percentages.
            git_config: Optional git configuration settings.
            include_css: When ``False`` and generating HTML omit embedded style
                block. Defaults to ``True`` when unspecified.

        Returns:
            str: The formatted output string.

        Raises:
            ValueError: If the format_type is not supported.
        """
        if isinstance(data, ComparisonResult):
            return Formatter._format_comparison(
                data, format_type, display_config, include_css=include_css
            )
        else:
            return Formatter._format_metrics(
                data,
                format_type,
                git_info,
                display_config,
                git_config,
                include_css=include_css,
            )

    @staticmethod
    def _format_metrics(
        metrics: Metrics,
        format_type: str | None = "table",
        git_info: GitInfo | None = None,
        display_config: DisplayConfig | None = None,
        git_config: GitConfig | None = None,
        include_css: bool | None = None,
    ) -> str:
        """Format a Metrics object based on the requested format type.

        Args:
            metrics: The Metrics object to display.
            format_type: The format identifier.
            git_info: Optional Git repository metadata.
            display_config: Display customization options for paths and percentages.
            git_config: Optional git configuration settings.
            include_css: When ``False`` and producing HTML omit embedded stylesheet.

        Returns:
            str: The formatted output string.

        Raises:
            ValueError: If the format_type is not supported.
        """
        if format_type is None or format_type == "table":
            return TableFormatter(display_config, git_config).format(
                metrics, git_info=git_info
            )
        elif format_type == "json":
            return JsonFormatter(display_config).format(metrics, git_info=git_info)
        elif format_type in {"markdown", "md"}:
            return MarkdownFormatter(display_config, git_config).format(
                metrics, git_info=git_info
            )
        elif format_type == "html":
            # determine whether to include CSS; default to True when unset
            css_flag = include_css if include_css is not None else True
            return HtmlFormatter(
                display_config, git_config, include_css=css_flag
            ).format(metrics, git_info=git_info)
        else:
            raise ValueError(f"Unknown format type: {format_type}")

    @staticmethod
    def _format_comparison(
        comparison: ComparisonResult,
        format_type: str | None = "table",
        display_config: DisplayConfig | None = None,
        include_css: bool | None = None,
    ) -> str:
        """Format a ComparisonResult object based on the requested format type.

        Args:
            comparison: The ComparisonResult object to display.
            format_type: The format identifier (table, json, md).
            display_config: Display customization options for paths and percentages.
            include_css: When ``False`` and producing HTML omit embedded stylesheet.

        Returns:
            str: The formatted output string.

        Raises:
            ValueError: If the format_type is not supported.
        """
        if format_type is None or format_type == "table":
            return CompareFormatter(display_config).format_table(comparison)
        elif format_type == "json":
            return CompareFormatter().format_json(comparison)
        elif format_type in {"markdown", "md"}:
            return CompareFormatter(display_config).format_markdown(comparison)
        elif format_type == "html":
            # simple HTML wrapper around markdown; preserve style toggle

            md = CompareFormatter(display_config).format_markdown(comparison)
            css_flag = include_css if include_css is not None else True
            parts: list[str] = [
                "<!DOCTYPE html>",
                '<html lang="en">',
                "<head>",
                '<meta charset="utf-8"/><title>Comparison</title>',
            ]
            if css_flag:
                parts.append(
                    "<style>"
                    "body{font-family:Arial,Helvetica,sans-serif;margin:1em;}"
                    "pre{white-space:pre-wrap;font-family:inherit;}"
                    "</style>"
                )
            parts.append("</head>")
            parts.append("<body>")
            parts.append(f"<pre>{escape(md)}</pre>")
            parts.append("</body>")
            parts.append("</html>")
            return "\n".join(parts)
        else:
            raise ValueError(f"Unknown format type: {format_type}")
