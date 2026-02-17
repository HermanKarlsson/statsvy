"""Formatter module for Markdown output."""

from statsvy.data.config import DisplayConfig, GitConfig
from statsvy.data.git_info import GitInfo
from statsvy.data.metrics import Metrics
from statsvy.data.project_info import DependencyInfo
from statsvy.utils.formatting import format_size, truncate_path_display


class MarkdownFormatter:
    """Formats Metrics objects as Markdown strings."""

    def __init__(
        self,
        display_config: DisplayConfig | None = None,
        git_config: GitConfig | None = None,
    ) -> None:
        """Initialize formatter with display preferences.

        Args:
            display_config: Optional display configuration overrides.
            git_config: Optional git configuration settings.
        """
        self._truncate_paths = (
            display_config.truncate_paths if display_config else False
        )
        self._show_percentages = (
            display_config.show_percentages if display_config else True
        )
        self._show_contributors = git_config.show_contributors if git_config else True

    def format(self, metrics: Metrics, git_info: GitInfo | None = None) -> str:
        """Format metrics data as a Markdown string.

        Args:
            metrics: The Metrics object to format.
            git_info: Optional Git repository metadata to include.

        Returns:
            str: A Markdown document representing the metrics.
        """
        parts: list[str] = []

        parts.append(f"# Scan: {metrics.name}\n")
        parts.append(self._format_summary(metrics, git_info))

        if hasattr(metrics, "lines_by_category") and metrics.lines_by_category:
            parts.append(self._format_category_table(metrics))

        if metrics.lines_by_lang:
            parts.append(self._format_language_table(metrics))

        if metrics.dependencies is not None:
            parts.append(self._format_dependencies(metrics.dependencies))

        return "\n".join(parts)

    def _format_summary(self, metrics: Metrics, git_info: GitInfo | None) -> str:
        """Build the summary section with general project statistics.

        Args:
            metrics: The Metrics object to summarise.
            git_info: Optional Git repository metadata to include.

        Returns:
            str: A Markdown section with project statistics.
        """
        path_value = (
            truncate_path_display(metrics.path)
            if self._truncate_paths
            else str(metrics.path)
        )

        # Prefer explicit byte field but tolerate test-mocks that only provide
        # KB/MB attributes. Use runtime type-checking so MagicMock attributes
        # (which are truthy) do not accidentally bypass fallbacks.
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

        lines = [
            "## Project Statistics\n",
            "| Field | Value |",
            "|-------|-------|",
            f"| Path | `{path_value}` |",
            f"| Timestamp | {metrics.timestamp.strftime('%Y-%m-%d')} |",
            f"| Files | {metrics.total_files:,} |",
            f"| Size | {format_size(bytes_val or 0)} |",
            f"| Total Lines | {metrics.total_lines:,} |",
        ]

        if git_info is not None:
            repo_label = "Yes" if git_info.is_git_repo else "No"
            commit_count = (
                git_info.commit_count if git_info.commit_count is not None else "-"
            )
            contributors = (
                ", ".join(git_info.contributors) if git_info.contributors else "-"
            )
            branches = ", ".join(git_info.branches) if git_info.branches else "-"
            last_commit = git_info.last_commit_date or "-"
            commits_per_month = (
                f"{git_info.commits_per_month_all_time:.1f}"
                if git_info.commits_per_month_all_time is not None
                else "-"
            )
            commits_30d = (
                git_info.commits_last_30_days
                if git_info.commits_last_30_days is not None
                else "-"
            )
            git_lines = [
                f"| Git Repo | {repo_label} |",
                f"| Git Branch | {git_info.current_branch or '-'} |",
                f"| Git Remote | {git_info.remote_url or '-'} |",
                f"| Git Commits | {commit_count} |",
            ]

            if self._show_contributors:
                git_lines.append(f"| Contributors | {contributors} |")

            git_lines.extend(
                [
                    f"| Last Commit | {last_commit} |",
                    f"| Branches | {branches} |",
                    f"| Commits/Month | {commits_per_month} |",
                    f"| Commits (30d) | {commits_30d} |",
                ]
            )

            lines.extend(git_lines)
        return "\n".join(lines)

    def _format_category_table(self, metrics: Metrics) -> str:
        """Build the lines-by-category Markdown table.

        Args:
            metrics: The Metrics object with category data.

        Returns:
            str: A Markdown table of lines grouped by category.
        """
        header = (
            "| Category | Lines | % |"
            if self._show_percentages
            else "| Category | Lines |"
        )
        divider = (
            "|----------|------:|--:|"
            if self._show_percentages
            else "|----------|------:|"
        )
        lines = [
            "\n## Lines of Code by Type\n",
            header,
            divider,
        ]

        sorted_cats = sorted(
            metrics.lines_by_category.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        for category, line_count in sorted_cats:
            display_name = category.title() if category != "unknown" else "Unknown"
            if self._show_percentages:
                percentage = (
                    (line_count / metrics.total_lines * 100)
                    if metrics.total_lines > 0
                    else 0
                )
                lines.append(f"| {display_name} | {line_count:,} | {percentage:.1f}% |")
            else:
                lines.append(f"| {display_name} | {line_count:,} |")

        return "\n".join(lines)

    def _format_language_table(self, metrics: Metrics) -> str:
        """Build the lines-by-language Markdown table.

        Args:
            metrics: The Metrics object with language data.

        Returns:
            str: A Markdown table of lines grouped by language.
        """
        if self._show_percentages:
            header = "| Language | Lines | % | Code | Comments | Blank |"
            divider = "|----------|------:|--:|-----:|---------:|------:|"
        else:
            header = "| Language | Lines | Code | Comments | Blank |"
            divider = "|----------|------:|-----:|---------:|------:|"
        lines = [
            "\n## Lines of Code by Language\n",
            header,
            divider,
        ]

        sorted_langs = sorted(
            metrics.lines_by_lang.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        for language, line_count in sorted_langs:
            comments = metrics.comment_lines_by_lang.get(language, 0)
            blanks = metrics.blank_lines_by_lang.get(language, 0)
            code = line_count - comments - blanks
            if self._show_percentages:
                percentage = (
                    (line_count / metrics.total_lines * 100)
                    if metrics.total_lines > 0
                    else 0
                )
                lines.append(
                    f"| {language} | {line_count:,} | {percentage:.1f}%"
                    f" | {code:,} | {comments} | {blanks} |"
                )
            else:
                lines.append(
                    f"| {language} | {line_count:,} | {code:,} | {comments} | "
                    f"{blanks} |"
                )

        return "\n".join(lines)

    def _format_dependencies(self, dep_info: DependencyInfo) -> str:
        """Format dependency section as Markdown.

        Args:
            dep_info: The DependencyInfo to format.

        Returns:
            str: A Markdown section with dependency information.
        """
        lines = [
            "## Dependencies\n",
            "| Category | Count |",
            "|----------|-------|",
            f"| Production | {dep_info.prod_count} |",
            f"| Development | {dep_info.dev_count} |",
            f"| Optional | {dep_info.optional_count} |",
            f"| **Total** | **{dep_info.total_count}** |",
        ]

        if dep_info.sources:
            lines.append(f"\nSources: {', '.join(dep_info.sources)}")

        if dep_info.conflicts:
            lines.append("\n### Conflicts\n")
            for conflict in dep_info.conflicts:
                lines.append(f"- {conflict}")

        return "\n".join(lines)
