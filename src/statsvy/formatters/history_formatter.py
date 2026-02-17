"""Formatter module for displaying scan history as Rich terminal output."""

from datetime import datetime
from typing import Any

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from statsvy.utils.console import console
from statsvy.utils.formatting import delta_str

HistoryEntry = dict[str, Any]


def _parse_time(entry: HistoryEntry) -> datetime:
    """Parse the ``time`` field of a history entry into a :class:`datetime`.

    Args:
        entry: A single history entry dict.

    Returns:
        The parsed datetime object.
    """
    return datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S")


class HistoryFormatter:
    """Formats a list of history entries as a pretty Rich terminal table.

    Each row in the output table corresponds to one scan entry from the
    history JSON file, showing key metrics and delta values compared to
    the immediately preceding entry.

    Example::

        formatter = HistoryFormatter()
        print(formatter.format(entries))
    """

    HEADER_COLOR = "bold khaki1"
    LABEL_COLOR = "bold cyan"
    VALUE_COLOR = "bright_white"
    ACCENT_COLOR = "spring_green3"
    BORDER_COLOR = "grey37"

    def format(self, entries: list[HistoryEntry]) -> str:
        """Format a list of history entries as a Rich terminal string.

        Args:
            entries: Ordered list of history entry dicts (oldest first).

        Returns:
            A string containing Rich-rendered terminal output.
        """
        output_parts: list[str] = []

        header_text = Text(" Scan History ", style=self.HEADER_COLOR)
        header_panel = Panel(
            header_text,
            expand=False,
            border_style=self.HEADER_COLOR,
            box=box.DOUBLE_EDGE,
        )
        with console.capture() as capture:
            console.print(header_panel)
        output_parts.append(capture.get())

        if not entries:
            with console.capture() as capture:
                console.print("[grey50]No history entries to display.[/grey50]")
            output_parts.append(capture.get())
            return "".join(output_parts)

        history_table = self._create_history_table(entries)
        with console.capture() as capture:
            console.print(history_table)
        output_parts.append(capture.get())

        return "".join(output_parts)

    def _create_history_table(self, entries: list[HistoryEntry]) -> Table:
        """Build the main Rich :class:`~rich.table.Table` for all history entries.

        Each row represents one scan. Delta columns compare each entry
        against the one directly before it in the list.

        Args:
            entries: Ordered list of history entry dicts (oldest first).

        Returns:
            A configured :class:`~rich.table.Table` ready for rendering.
        """
        table = Table(
            title="[bold white]Scan History[/bold white]",
            title_justify="left",
            show_header=True,
            header_style=f"bold {self.HEADER_COLOR}",
            border_style=self.BORDER_COLOR,
            box=box.ROUNDED,
        )

        table.add_column("#", justify="right", style="grey50", no_wrap=True)
        table.add_column("Timestamp", style=self.LABEL_COLOR, no_wrap=True)
        table.add_column("Files", justify="right", style=self.VALUE_COLOR)
        table.add_column("Δ Files", justify="right")
        table.add_column(
            "Total Lines", justify="right", style=f"bold {self.ACCENT_COLOR}"
        )
        table.add_column("Δ Lines", justify="right")
        table.add_column("Size", justify="right", style=self.VALUE_COLOR)
        table.add_column("Programming", justify="right", style=self.VALUE_COLOR)
        table.add_column("Δ Prog", justify="right")
        table.add_column("Data", justify="right", style=self.VALUE_COLOR)
        table.add_column("Δ Data", justify="right")

        prev: HistoryEntry | None = None

        for idx, entry in enumerate(entries, start=1):
            metrics: dict[str, Any] = entry["metrics"]
            prev_metrics: dict[str, Any] | None = (
                prev["metrics"] if prev is not None else None
            )

            timestamp = _parse_time(entry).strftime("%Y-%m-%d %H:%M:%S")

            total_files: int = metrics["total_files"]
            total_lines: int = metrics["total_lines"]
            total_size: str = metrics.get("total_size", "-")

            cats: dict[str, int] = metrics.get("lines_by_category", {})
            programming: int = cats.get("programming", 0)
            data: int = cats.get("data", 0)

            prev_files = prev_metrics["total_files"] if prev_metrics else None
            prev_lines = prev_metrics["total_lines"] if prev_metrics else None
            prev_prog = (
                prev_metrics.get("lines_by_category", {}).get("programming")
                if prev_metrics
                else None
            )
            prev_data = (
                prev_metrics.get("lines_by_category", {}).get("data")
                if prev_metrics
                else None
            )

            table.add_row(
                str(idx),
                timestamp,
                f"{total_files:,}",
                delta_str(total_files, prev_files),
                f"{total_lines:,}",
                delta_str(total_lines, prev_lines),
                total_size,
                f"{programming:,}",
                delta_str(programming, prev_prog),
                f"{data:,}",
                delta_str(data, prev_data),
            )

            prev = entry

        return table
