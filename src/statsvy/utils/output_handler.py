"""Output handling for formatted results."""

from pathlib import Path

from rich.text import Text

from statsvy.data.config import Config
from statsvy.utils.console import console


class OutputHandler:
    """Handles presentation and storage of formatted output."""

    @staticmethod
    def handle(
        formatted_output: str,
        output_path: Path | None,
        config: Config | None = None,
    ) -> None:
        """Handle presentation and storage of results.

        If an output path is provided, saves the formatted output to a file.
        Otherwise, prints it to standard output.

        Args:
            formatted_output: The formatted output string to handle.
            output_path: Path to save output file, or None to print to console.
            config: Optional Config instance for verbose logging.
        """
        config = config or Config.default()

        if output_path:
            OutputHandler._save_to_file(formatted_output, output_path, config)
        else:
            OutputHandler._print_to_console(formatted_output)

    @staticmethod
    def _save_to_file(
        formatted_output: str,
        output_path: Path,
        config: Config,
    ) -> None:
        """Save formatted output to a file.

        Args:
            formatted_output: The formatted output string to save.
            output_path: Path to save the output file.
            config: Config instance for verbose logging.
        """
        try:
            output_path.write_text(formatted_output)
        except OSError as exc:
            console.print(
                Text(f"Failed to save output to {output_path}: {exc}", style="red")
            )
            raise

        if config.core.verbose:
            console.print(Text("Saved to ") + Text(str(output_path), style="cyan"))

        console.print(f"[green]Output saved to {output_path}[/green]")

    @staticmethod
    def _print_to_console(formatted_output: str) -> None:
        """Print formatted output to console.

        Args:
            formatted_output: The formatted output string to print.
        """
        # Print is intentional to emit raw output for piping.
        print(formatted_output)  # noqa: T201
