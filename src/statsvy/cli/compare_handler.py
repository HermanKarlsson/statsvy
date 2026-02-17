"""Compare command orchestration and execution."""

from pathlib import Path
from time import perf_counter

from rich import inspect
from rich.text import Text

from statsvy.core.comparison import ComparisonAnalyzer
from statsvy.core.formatter import Formatter
from statsvy.data.config import Config
from statsvy.data.metrics import Metrics
from statsvy.serializers.metrics_serializer import MetricsSerializer
from statsvy.storage.history_storage import HistoryStorage
from statsvy.utils.console import console
from statsvy.utils.output_handler import OutputHandler


class CompareHandler:
    """Orchestrates the compare command workflow.

    Coordinates loading metrics from two projects, performing comparison,
    and formatting the results.
    """

    def __init__(self, config: Config) -> None:
        """Initialize compare handler.

        Args:
            config: Configuration instance controlling comparison behavior.
        """
        self.config = config

    def execute(
        self,
        project1_path: str,
        project2_path: str,
        output_format: str | None,
        output_path: Path | None,
    ) -> None:
        """Execute the complete comparison workflow.

        Args:
            project1_path: Path to the first project directory.
            project2_path: Path to the second project directory.
            output_format: Desired output format (table, json, md).
            output_path: Path to save output, or None to print to console.

        Raises:
            FileNotFoundError: If either project has no history.
            SystemExit: If comparison fails.
        """
        if self.config.core.verbose:
            inspect(self.config)
            console.print("")

        start = perf_counter()

        # Load metrics from both projects
        try:
            metrics1 = self._load_project_metrics(Path(project1_path))
            metrics2 = self._load_project_metrics(Path(project2_path))
        except FileNotFoundError as e:
            console.print(Text(f"Error: {e}", style="red bold"))
            raise SystemExit(1) from e

        # Perform comparison
        comparison = ComparisonAnalyzer.compare(metrics1, metrics2)

        # Format results
        try:
            formatted_output = Formatter.format(
                comparison,
                output_format,
                display_config=self.config.display,
            )
        except ValueError as e:
            console.print(Text(f"Error: {e}", style="red"))
            raise SystemExit(1) from e

        # Handle output
        end = perf_counter()
        if self.config.core.verbose:
            console.print(f"Statsvy comparison completed in {end - start:.2f} seconds")

        OutputHandler.handle(formatted_output, output_path, self.config)

    def _load_project_metrics(self, project_path: Path) -> Metrics:
        """Load the latest metrics from a project's history file.

        Args:
            project_path: The root directory of the project.

        Returns:
            The latest Metrics object from the project's history.

        Raises:
            FileNotFoundError: If the project has no history or no entries.
        """
        history_file = project_path / ".statsvy" / "history.json"

        if not history_file.exists():
            raise FileNotFoundError(
                f"No history found for project at {project_path}. "
                "Run 'statsvy scan' first to initialize history."
            )

        history_entries = HistoryStorage.load_history(history_file, self.config)

        if not history_entries:
            raise FileNotFoundError(
                f"History file at {history_file} is empty. "
                "Run 'statsvy scan' first to initialize history."
            )

        # Get the latest entry
        latest_entry = history_entries[-1]
        metrics_dict = latest_entry.get("metrics", {})

        # Convert dict back to Metrics object
        return MetricsSerializer.from_dict(metrics_dict)
