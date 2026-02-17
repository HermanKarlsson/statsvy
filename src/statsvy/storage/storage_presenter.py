"""Presentation layer for storage data (history and project info)."""

import json
from pathlib import Path
from typing import Any

from statsvy.formatters.history_formatter import HistoryFormatter
from statsvy.formatters.summary_formatter import SummaryFormatter
from statsvy.storage.history_storage import HistoryStorage
from statsvy.storage.project_metadata_storage import ProjectMetadataStorage
from statsvy.utils.console import console


class StoragePresenter:
    """Handles display of stored project and history data."""

    @staticmethod
    def show_current() -> None:
        """Display detailed data for the currently tracked project.

        Prints project metadata from project.json and scan-related details
        from history.json when available.
        """
        stats_dir = Path.cwd() / ".statsvy"

        if not stats_dir.exists():
            console.print(
                "[yellow]No tracked project found. Run 'statsvy track' first.[/yellow]"
            )
            return

        project_file = stats_dir / "project.json"
        if not project_file.exists():
            console.print(
                "[yellow]No project metadata found. Run 'statsvy track' first.[/yellow]"
            )
            return

        project_data = ProjectMetadataStorage.load_project_data(project_file)
        if project_data is None:
            console.print("[red]project.json is not valid JSON.[/red]")
            return

        history_file = stats_dir / "history.json"
        history_data = HistoryStorage.load_history(history_file)

        latest_time, latest_metrics = StoragePresenter._extract_latest_details(
            history_data
        )

        last_scan = project_data.get("last_scan")
        if not last_scan:
            last_scan = latest_time

        SummaryFormatter.format(
            project_data=project_data,
            history_data=history_data,
            last_scan=last_scan,
            latest_metrics=latest_metrics,
        )

    @staticmethod
    def show_latest() -> None:
        """Display the results from the latest scan.

        Raises:
            FileNotFoundError: If the history file does not exist.
            json.JSONDecodeError: If the history file is not valid JSON.
            IndexError: If the history file contains no entries.
            KeyError: If the history entry is missing expected keys.
        """
        history_file = Path.cwd() / ".statsvy" / "history.json"

        with open(history_file) as f:
            data: Any = json.load(f)

        last_entry = data[-1]
        console.print(
            f"Last scan time: {last_entry['time']}\n"
            + f"Total files: {last_entry['metrics']['total_files']}\n"
            + f"Total size: {last_entry['metrics']['total_size']}"
        )

    @staticmethod
    def show_history() -> None:
        """Retrieve and display the full scan history using the formatter.

        Raises:
            FileNotFoundError: If the history file does not exist.
            json.JSONDecodeError: If the history file is not valid JSON.
        """
        history_file = Path.cwd() / ".statsvy" / "history.json"

        with open(history_file) as f:
            data: Any = json.load(f)

        # Print is intentional to emit raw formatted output for piping.
        print(HistoryFormatter().format(data))  # noqa: T201

    @staticmethod
    def _extract_latest_details(
        history_data: list[Any],
    ) -> tuple[str | None, dict[str, Any]]:
        """Extract the latest timestamp and metrics from history.

        Args:
            history_data: Parsed history entries.

        Returns:
            A tuple with latest time and latest metrics dictionary.
        """
        latest_entry = history_data[-1] if history_data else None
        latest_time: str | None = None
        latest_metrics: dict[str, Any] = {}

        if isinstance(latest_entry, dict):
            latest_time = latest_entry.get("time")
            candidate = latest_entry.get("metrics", {})
            if isinstance(candidate, dict):
                latest_metrics = candidate

        return latest_time, latest_metrics
