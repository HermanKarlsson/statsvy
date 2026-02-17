"""Formatter module for displaying project and data summaries as Rich output."""

from typing import Any

from rich.text import Text

from statsvy.utils.console import console


class SummaryFormatter:
    """Formats project metadata and history summaries as Rich text output."""

    @staticmethod
    def format(
        project_data: dict[str, Any],
        history_data: list[Any],
        last_scan: str | None,
        latest_metrics: dict[str, Any],
    ) -> None:
        """Display a formatted project summary with latest metrics.

        Prints project metadata, scan history count, and most recent scan
        statistics in a user-friendly Rich format. Git metadata is included
        when present in ``project_data``.

        Args:
            project_data: Project metadata dict (name, path, date_added).
            history_data: List of history entries from history.json.
            last_scan: Timestamp of the most recent scan, or None.
            latest_metrics: Metrics dict from the most recent scan entry.
        """
        console.print(Text("Current Project", style="bold"))
        console.print(f"Name: {project_data.get('name', '-')}")
        console.print(f"Path: {project_data.get('path', '-')}")
        console.print(f"Date added: {project_data.get('date_added', '-')}")
        console.print(f"Last scan: {last_scan or '-'}")
        console.print(f"Total scans: {len(history_data)}")

        SummaryFormatter._print_git_info(project_data)
        SummaryFormatter._print_latest_metrics(latest_metrics)

        if "dependencies" in latest_metrics:
            SummaryFormatter._print_dependencies_info(latest_metrics["dependencies"])

    @staticmethod
    def _print_git_info(project_data: dict[str, Any]) -> None:
        """Print Git repository information if available.

        Args:
            project_data: Project metadata dict containing optional git_info.
        """
        git_info = project_data.get("git_info")
        if not isinstance(git_info, dict):
            return

        # Format git repo status
        repo_status = {True: "Yes", False: "No"}.get(git_info.get("is_git_repo"), "-")
        console.print(f"Git repo: {repo_status}")

        # Format branch info
        branch = git_info.get("current_branch") or "-"
        console.print(f"Git branch: {branch}")

        remote = git_info.get("remote_url") or "-"
        console.print(f"Git remote: {remote}")

        # Format commit count
        commit_count = git_info.get("commit_count")
        console.print(
            f"Git commits: {commit_count if commit_count is not None else '-'}"
        )

        # Format contributors list
        contributors = git_info.get("contributors")
        contributors_str = ", ".join(contributors) if contributors else "-"
        console.print(f"Contributors: {contributors_str}")

        # Format git metrics
        last_commit = git_info.get("last_commit_date") or "-"
        console.print(f"Last commit: {last_commit}")

        branches = git_info.get("branches")
        branches_str = ", ".join(branches) if branches else "-"
        console.print(f"Branches: {branches_str}")

        commits_per_month = git_info.get("commits_per_month_all_time")
        cpm_str = f"{commits_per_month:.1f}" if commits_per_month is not None else "-"
        console.print(f"Commits/month (avg): {cpm_str}")

        commits_30d = git_info.get("commits_last_30_days")
        console.print(
            f"Commits (30d): {commits_30d if commits_30d is not None else '-'}"
        )

    @staticmethod
    def _print_latest_metrics(latest_metrics: dict[str, Any]) -> None:
        """Print the latest metrics from most recent scan.

        Args:
            latest_metrics: Metrics dict from the most recent scan entry.
        """
        if not latest_metrics:
            return

        latest_total_files = latest_metrics.get("total_files", "-")
        latest_total_size = latest_metrics.get("total_size", "-")
        latest_total_lines = latest_metrics.get("total_lines", "-")

        console.print(f"Latest total files: {latest_total_files}")
        console.print(f"Latest total size: {latest_total_size}")
        console.print(f"Latest total lines: {latest_total_lines}")

    @staticmethod
    def _print_dependencies_info(deps_info: dict[str, Any]) -> None:
        """Print dependency analysis information if available.

        Args:
            deps_info: Dependency information dict from metrics.
        """
        if not deps_info:
            return

        console.print(f"Prod dependencies: {deps_info.get('prod_count', 0)}")
        console.print(f"Dev dependencies: {deps_info.get('dev_count', 0)}")
        console.print(f"Optional dependencies: {deps_info.get('optional_count', 0)}")
        console.print(f"Total dependencies: {deps_info.get('total_count', 0)}")

        conflicts = deps_info.get("conflicts", [])
        if conflicts:
            console.print(f"[yellow]Conflicts detected: {len(conflicts)}[/yellow]")
            for conflict in conflicts[:3]:
                console.print(f"  [yellow]- {conflict}[/yellow]")
            if len(conflicts) > 3:
                console.print(f"  [yellow]... and {len(conflicts) - 3} more[/yellow]")
