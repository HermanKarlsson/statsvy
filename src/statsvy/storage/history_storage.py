"""History file storage and retrieval operations."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.text import Text

from statsvy.data.config import Config
from statsvy.data.metrics import Metrics
from statsvy.formatters.json_formatter import JsonFormatter
from statsvy.utils.console import console


class HistoryStorage:
    """Manages persistence and retrieval of scan history."""

    @staticmethod
    def save_entry(
        history_file: Path, metrics: Metrics, config: Config | None = None
    ) -> None:
        """Save a new metrics entry to the history file.

        Args:
            history_file: Path to the history.json file.
            metrics: The Metrics object to persist.
            config: Optional Config instance for storage settings.
        """
        config = config or Config.default()

        new_entry = HistoryStorage._build_entry(metrics)
        history_data = HistoryStorage.load_history(history_file, config)

        history_data.append(new_entry)

        HistoryStorage._write_history(history_file, history_data, config)

    @staticmethod
    def load_history(history_file: Path, config: Config | None = None) -> list[Any]:
        """Load the history data from a JSON file, handling legacy formats.

        Args:
            history_file: Path to the history.json file.
            config: Optional Config instance for verbose logging.

        Returns:
            A list of historical scan entries.
        """
        config = config or Config.default()

        if not history_file.exists():
            if config.core.verbose:
                console.print(f"Creating new history file: {history_file}")
            return []

        try:
            content = history_file.read_text()
            loaded = json.loads(content) if content else []
            return HistoryStorage._process_loaded_history(loaded, config)
        except json.JSONDecodeError:
            if config.core.verbose:
                console.print(
                    Text(
                        "Warning: History file corrupted, starting fresh",
                        style="yellow",
                    )
                )
            return []

    @staticmethod
    def get_latest_entry(
        history_file: Path, config: Config | None = None
    ) -> dict[str, Any] | None:
        """Get the latest history entry.

        Args:
            history_file: Path to the history.json file.
            config: Optional Config instance for verbose logging.

        Returns:
            Latest history entry dict, or None if no entries exist.
        """
        history_data = HistoryStorage.load_history(history_file, config)
        return history_data[-1] if history_data else None

    @staticmethod
    def _build_entry(metrics: Metrics) -> dict[str, Any]:
        """Format metrics into a historical entry dictionary with a timestamp.

        Args:
            metrics: The Metrics object to be stored.

        Returns:
            A dictionary containing the timestamp and serialized metrics.
        """
        formatted_metrics = JsonFormatter().format(metrics)

        return {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metrics": json.loads(formatted_metrics),
        }

    @staticmethod
    def _process_loaded_history(
        loaded: dict[str, Any] | list[Any], config: Config
    ) -> list[Any]:
        """Process loaded history data, handling legacy formats.

        Args:
            loaded: The loaded history data.
            config: Config instance for verbose logging.

        Returns:
            List of history entries.
        """
        # Handle legacy single-entry format
        if isinstance(loaded, dict):
            if config.core.verbose:
                console.print("Converting legacy single-entry history format")
            return [loaded]

        if isinstance(loaded, list):
            if config.core.verbose:
                console.print(
                    Text("Loaded history with ")
                    + Text(f"{len(loaded)}", style="cyan")
                    + Text(" entries")
                )
            return loaded

        return []

    @staticmethod
    def _write_history(
        history_file: Path, history_data: list[Any], config: Config | None = None
    ) -> None:
        """Write the updated history list back to the JSON file.

        Args:
            history_file: Path to the target history.json file.
            history_data: The list of entries to persist.
            config: Optional Config instance for verbose logging.
        """
        config = config or Config.default()
        try:
            history_file.write_text(json.dumps(history_data, indent=2))
        except OSError as exc:
            console.print(
                Text(f"Failed to write history file {history_file}: {exc}", style="red")
            )
            raise

        if config.core.verbose:
            console.print(
                Text("Saved to ")
                + Text(str(history_file), style="cyan")
                + Text(f" ({len(history_data)} entries)")
            )
