"""Formatter module specifically for Rich terminal output."""

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from statsvy.data.config import DisplayConfig, GitConfig
from statsvy.data.git_info import GitInfo
from statsvy.data.metrics import Metrics
from statsvy.data.project_info import DependencyInfo
from statsvy.utils.console import console
from statsvy.utils.formatting import format_size, truncate_path_display


class TableFormatter:
    """Formats Metrics objects as pretty Rich terminal output."""

    HEADER_COLOR = "bold khaki1"
    LABEL_COLOR = "bold cyan"
    VALUE_COLOR = "bright_white"
    ACCENT_COLOR = "spring_green3"
    BORDER_COLOR = "grey37"

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
        self._show_deps_list = display_config.show_deps_list if display_config else True
        self._show_contributors = git_config.show_contributors if git_config else True

    def format(self, metrics: Metrics, git_info: GitInfo | None = None) -> str:
        """Format metrics data as a Rich terminal table string.

        Args:
            metrics: The Metrics object to format.
            git_info: Optional Git repository metadata to include.
        """
        header_text = Text(f" Scan: {metrics.name} ", style=self.HEADER_COLOR)
        header_panel = Panel(
            header_text,
            expand=False,
            border_style=self.HEADER_COLOR,
            box=box.DOUBLE_EDGE,
        )

        output_parts: list[str] = []
        self._append_table(output_parts, header_panel)

        info_table = self._create_info_table(metrics)
        self._append_table(output_parts, info_table)

        if git_info is not None:
            git_table = self._create_git_table(git_info)
            self._append_table(output_parts, git_table)

        if hasattr(metrics, "lines_by_category") and metrics.lines_by_category:
            cat_table = self._create_category_table(metrics)
            self._append_table(output_parts, cat_table)

        if metrics.lines_by_lang:
            lang_table = self._create_language_table(metrics)
            self._append_table(output_parts, lang_table)

        if metrics.dependencies is not None:
            deps_table = self._create_dependencies_table(metrics.dependencies)
            self._append_table(output_parts, deps_table)
            if self._show_deps_list and metrics.dependencies.dependencies:
                list_table = self._create_dep_list_table(metrics.dependencies)
                self._append_table(output_parts, list_table)

        return "".join(output_parts)

    @staticmethod
    def _append_table(output_parts: list[str], table: Panel | Table) -> None:
        """Capture table output and append to output parts.

        Args:
            output_parts: List of output strings to append to.
            table: Panel or Table object to capture and append.
        """
        with console.capture() as capture:
            console.print(table)
        output_parts.append(capture.get())

    def _create_info_table(self, metrics: Metrics) -> Table:
        """Create a table with general metrics information.

        Args:
            metrics: The Metrics object to format.
        """
        table = Table(
            title="[bold white]Project Statistics[/bold white]",
            title_justify="left",
            show_header=True,
            header_style=f"bold {self.HEADER_COLOR}",
            border_style=self.BORDER_COLOR,
            box=box.HEAVY_EDGE,
        )
        table.add_column("Details", style=self.VALUE_COLOR)

        path_value = (
            truncate_path_display(metrics.path)
            if self._truncate_paths
            else str(metrics.path)
        )
        table.add_row("Path", path_value)
        table.add_row("Timestamp", metrics.timestamp.strftime("%Y-%m-%d"))
        table.add_row("Files", f"{metrics.total_files:,}")
        # Display a human-readable size (prefer explicit bytes but
        # fall back to KB/MB attributes provided by some test fixtures).
        # Resolve bytes robustly so test fixtures using MagicMock don't
        # accidentally provide non-numeric attributes that evaluate truthy.
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
        table.add_row("Size", format_size(bytes_val or 0))
        line_style = f"bold {self.ACCENT_COLOR}"
        lines_text = f"[{line_style}]{metrics.total_lines:,}[/{line_style}]"
        table.add_row("Total Lines", lines_text)

        return table

    def _create_git_table(self, git_info: GitInfo) -> Table:
        """Create a table with Git repository details.

        Args:
            git_info: Git repository metadata to include.
        """
        table = Table(
            title="[bold white]Git Repository[/bold white]",
            title_justify="left",
            show_header=True,
            header_style=f"bold {self.HEADER_COLOR}",
            border_style=self.BORDER_COLOR,
            box=box.HEAVY_EDGE,
        )
        table.add_column("Details", style=self.VALUE_COLOR)

        repo_label = "Yes" if git_info.is_git_repo else "No"
        table.add_row("Git Repo", repo_label)
        table.add_row("Git Branch", git_info.current_branch or "-")
        table.add_row("Git Remote", git_info.remote_url or "-")

        commit_count = (
            str(git_info.commit_count) if git_info.commit_count is not None else "-"
        )
        table.add_row("Git Commits", commit_count)

        if self._show_contributors:
            if git_info.contributors:
                contributors_str = ", ".join(git_info.contributors)
                table.add_row("Contributors", contributors_str)
            else:
                table.add_row("Contributors", "-")

        last_date = git_info.last_commit_date or "-"
        table.add_row("Last Commit", last_date)

        if git_info.branches:
            branches_str = ", ".join(git_info.branches)
            table.add_row("Branches", branches_str)
        else:
            table.add_row("Branches", "-")

        commits_per_month = (
            f"{git_info.commits_per_month_all_time:.1f}"
            if git_info.commits_per_month_all_time is not None
            else "-"
        )
        table.add_row("Commits/Month (avg)", commits_per_month)

        commits_30d = (
            str(git_info.commits_last_30_days)
            if git_info.commits_last_30_days is not None
            else "-"
        )
        table.add_row("Commits (30d)", commits_30d)

        return table

    def _create_category_table(self, metrics: Metrics) -> Table:
        """Create a table with line counts grouped by category."""
        table = Table(
            title="[bold white]Lines of Code by Type[/bold white]",
            title_justify="left",
            show_header=True,
            header_style=f"bold {self.HEADER_COLOR}",
            border_style=self.BORDER_COLOR,
            box=box.ROUNDED,
        )

        table.add_column("Category", style=self.LABEL_COLOR)
        table.add_column("Lines", justify="right", style=self.VALUE_COLOR)
        if self._show_percentages:
            table.add_column("%", justify="right", style=self.ACCENT_COLOR)

        sorted_cats = sorted(
            metrics.lines_by_category.items(), key=lambda x: x[1], reverse=True
        )

        for category, line_count in sorted_cats:
            display_name = category.title() if category != "unknown" else "Unknown"

            if self._show_percentages:
                percentage = (
                    (line_count / metrics.total_lines * 100)
                    if metrics.total_lines > 0
                    else 0
                )
                table.add_row(
                    display_name,
                    f"{line_count:,}",
                    f"{percentage:.1f}%",
                )
            else:
                table.add_row(display_name, f"{line_count:,}")

        return table

    def _create_language_table(self, metrics: Metrics) -> Table:
        """Create a table with language-specific line counts."""
        table = Table(
            title="[bold white]Lines of Code by Language[/bold white]",
            title_justify="left",
            show_header=True,
            header_style=f"bold {self.HEADER_COLOR}",
            border_style=self.BORDER_COLOR,
            box=box.ROUNDED,
        )

        table.add_column("Language", style=self.LABEL_COLOR)
        table.add_column("Lines", justify="right", style=self.VALUE_COLOR)
        if self._show_percentages:
            table.add_column("%", justify="right", style=self.ACCENT_COLOR)
        table.add_column("Code", justify="right", style=self.VALUE_COLOR)
        table.add_column("Comments", justify="right", style="bright_magenta")
        table.add_column("Blank", justify="right", style="bright_blue")

        sorted_langs = sorted(
            metrics.lines_by_lang.items(), key=lambda x: x[1], reverse=True
        )

        for language, line_count in sorted_langs:
            comments = metrics.comment_lines_by_lang.get(language, 0)
            blanks = metrics.blank_lines_by_lang.get(language, 0)
            code_only = line_count - comments - blanks

            if self._show_percentages:
                percentage = (
                    (line_count / metrics.total_lines * 100)
                    if metrics.total_lines > 0
                    else 0
                )
                table.add_row(
                    language,
                    f"{line_count:,}",
                    f"{percentage:.1f}%",
                    f"{code_only:,}",
                    str(comments),
                    str(blanks),
                )
            else:
                table.add_row(
                    language,
                    f"{line_count:,}",
                    f"{code_only:,}",
                    str(comments),
                    str(blanks),
                )

        return table

    def _create_dependencies_table(self, dep_info: DependencyInfo) -> Table:
        """Create a table with dependency summary information.

        Args:
            dep_info: The DependencyInfo object to format.
        """
        table = Table(
            title="[bold white]Dependencies[/bold white]",
            title_justify="left",
            show_header=True,
            header_style=f"bold {self.HEADER_COLOR}",
            border_style=self.BORDER_COLOR,
            box=box.HEAVY_EDGE,
        )
        table.add_column("Details", style=self.VALUE_COLOR)

        table.add_row("Production", f"{dep_info.prod_count}")
        table.add_row("Development", f"{dep_info.dev_count}")
        table.add_row("Optional", f"{dep_info.optional_count}")
        table.add_row("Total", f"[bold {self.ACCENT_COLOR}]{dep_info.total_count}")
        table.add_row(
            "Sources", ", ".join(dep_info.sources) if dep_info.sources else "-"
        )

        if dep_info.conflicts:
            conflict_str = (
                "\n".join(dep_info.conflicts)
                if len(dep_info.conflicts) <= 3
                else "\n".join(dep_info.conflicts[:3])
                + f"\n... and {len(dep_info.conflicts) - 3} more"
            )
            table.add_row(
                "[bold yellow]Conflicts[/bold yellow]",
                f"[bold yellow]{conflict_str}[/bold yellow]",
            )

        return table

    def _create_dep_list_table(self, dep_info: DependencyInfo) -> Table:
        """Create a table listing every individual dependency.

        Args:
            dep_info: The DependencyInfo object to format.
        """
        _category_label = {
            "prod": "Production",
            "dev": "Development",
            "optional": "Optional",
        }
        _category_order = {"prod": 0, "dev": 1, "optional": 2}

        table = Table(
            title="[bold white]Dependency List[/bold white]",
            title_justify="left",
            show_header=True,
            header_style=f"bold {self.HEADER_COLOR}",
            border_style=self.BORDER_COLOR,
            box=box.ROUNDED,
        )
        table.add_column("Name", style=self.LABEL_COLOR)
        table.add_column("Version", style=self.VALUE_COLOR)
        table.add_column("Category", style=self.ACCENT_COLOR)

        sorted_deps = sorted(
            dep_info.dependencies,
            key=lambda d: (_category_order.get(d.category, 99), d.name.lower()),
        )
        for dep in sorted_deps:
            label = _category_label.get(dep.category, dep.category.title())
            table.add_row(dep.name, dep.version or "-", label)

        return table
