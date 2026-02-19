"""Scan command orchestration and execution."""

from dataclasses import replace
from pathlib import Path
from time import perf_counter

import click
from rich import inspect
from rich.text import Text

from statsvy.core.analyzer import Analyzer
from statsvy.core.formatter import Formatter
from statsvy.core.git_stats import GitStats
from statsvy.core.performance_tracker import PerformanceTracker
from statsvy.core.project_scanner import ProjectScanner
from statsvy.core.scanner import Scanner
from statsvy.data.config import Config
from statsvy.data.metrics import Metrics
from statsvy.formatters.performance_metrics_formatter import PerformanceMetricsFormatter
from statsvy.storage.storage import Storage
from statsvy.utils.console import console
from statsvy.utils.output_handler import OutputHandler
from statsvy.utils.path_resolver import PathResolver
from statsvy.utils.timeout_checker import TimeoutChecker


class ScanHandler:
    """Orchestrates the scan command workflow.

    Coordinates scanning, analysis, formatting, and storage of metrics
    for a target directory.
    """

    def __init__(self, config: Config) -> None:
        """Initialize scan handler.

        Args:
            config: Configuration instance controlling scan behavior.
        """
        self.config = config

    def execute(
        self,
        target_dir: str | None,
        ignore_patterns: tuple[str, ...],
        output_format: str | None,
        output_path: Path | None,
    ) -> None:
        """Execute the complete scan workflow.

        Delegates setup/teardown and error handling to small helpers so
        the public surface remains easy to follow and within complexity
        limits.

        Args:
            target_dir: Optional path to the directory to scan. When None,
                the current working directory or tracked project is used.
            ignore_patterns: Glob patterns to exclude from the scan.
            output_format: Desired output format (e.g., 'table', 'json').
            output_path: Optional path for saving formatted output to file.

        Raises:
            TimeoutError: If the scan or analysis exceeds the configured
                timeout limit.
        """
        if self.config.core.verbose:
            inspect(self.config)
            console.print("")  # Blank line for readability

        start = perf_counter()

        perf_tracker = self._maybe_setup_performance_tracker()

        resolved_dir = PathResolver.get_target_directory(target_dir)
        combined_ignore = self._combine_ignore_patterns(ignore_patterns)

        self._log_scan_start(resolved_dir, combined_ignore)

        # When performance tracking is actually running we disable the
        # runtime timeout so profiling is not interrupted.
        effective_timeout = 0 if perf_tracker else self.config.scan.timeout_seconds
        timeout_checker = TimeoutChecker(effective_timeout)
        timeout_checker.start()

        metrics = self._run_scan_with_timeout(
            resolved_dir, combined_ignore, timeout_checker, perf_tracker
        )

        perf_metrics = perf_tracker.stop() if perf_tracker else None

        end = perf_counter()
        console.print(f"Scan completed in {end - start:.2f} seconds")

        if perf_metrics:
            console.print(PerformanceMetricsFormatter.format_text(perf_metrics))

        formatted = self._format_metrics(metrics, output_format)

        if self.config.storage.auto_save:
            Storage.save(metrics, config=self.config)

        OutputHandler.handle(formatted, output_path, self.config)

    def _maybe_setup_performance_tracker(self) -> PerformanceTracker | None:
        """Prompt user and (optionally) start a PerformanceTracker.

        Returns the running tracker or None when disabled/declined.
        """
        if not self.config.core.track_performance:
            return None

        console.print(
            Text(
                "Warning: enabling performance tracking will significantly "
                "slow the scan and increase memory usage.",
                style="yellow",
            )
        )

        try:
            proceed = click.confirm("Proceed with performance tracking?", default=False)
        except (EOFError, KeyboardInterrupt, click.Abort):
            proceed = False

        if proceed:
            tracker = PerformanceTracker()
            tracker.start()
            return tracker

        # User declined — disable for this run and continue.
        self.config = replace(
            self.config, core=replace(self.config.core, track_performance=False)
        )
        return None

    def _run_scan_with_timeout(
        self,
        resolved_dir: Path,
        combined_ignore: tuple[str, ...],
        timeout_checker: TimeoutChecker,
        perf_tracker: PerformanceTracker | None,
    ) -> Metrics:
        """Run scan/analysis and handle TimeoutError cleanup."""
        try:
            return self._scan_and_analyze(
                resolved_dir, combined_ignore, timeout_checker
            )
        except TimeoutError as e:
            if perf_tracker:
                perf_tracker.stop()
            console.print(f"[bold red]Error:[/bold red] {e}")
            console.print(
                "[yellow]Hint:[/yellow] Increase timeout with "
                "--scan-timeout or STATSVY_SCAN_TIMEOUT_SECONDS"
            )
            raise

    def _combine_ignore_patterns(self, cli_ignore: tuple[str, ...]) -> tuple[str, ...]:
        """Combine ignore patterns from CLI and configuration.

        Args:
            cli_ignore: Ignore patterns from CLI arguments.

        Returns:
            Combined tuple of ignore patterns.
        """
        config_patterns = self.config.scan.ignore_patterns
        return tuple(cli_ignore + config_patterns)

    def _log_scan_start(
        self, target_dir: Path, ignore_patterns: tuple[str, ...]
    ) -> None:
        """Log scan start information in verbose mode.

        Args:
            target_dir: The resolved target directory.
            ignore_patterns: Combined ignore patterns.
        """
        if self.config.core.verbose:
            console.print(
                Text("Target directory: ") + Text(str(target_dir), style="cyan")
            )
            if ignore_patterns:
                console.print(
                    Text("Ignore patterns: ")
                    + Text(str(len(ignore_patterns)), style="cyan")
                )

        console.print(f"Scanning directory [bold green]{target_dir}[/bold green]")

    def _scan_and_analyze(
        self,
        target_dir: Path,
        ignore_patterns: tuple[str, ...],
        timeout_checker: TimeoutChecker,
    ) -> Metrics:
        """Perform directory scan and file analysis.

        Args:
            target_dir: Directory to scan.
            ignore_patterns: Patterns to exclude.
            timeout_checker: Timeout checker to enforce time limits.

        Returns:
            Metrics object with analysis results.

        Raises:
            TimeoutError: If scan or analysis exceeds timeout limit.
        """
        # Scan directory
        scanner = Scanner(
            target_dir,
            ignore=ignore_patterns,
            no_gitignore=not self.config.scan.respect_gitignore,
            config=self.config,
        )
        scan_result = scanner.scan(timeout_checker)

        # Analyze files
        # Navigate from src/statsvy/cli/scan_handler.py to project root
        package_dir = Path(__file__).parent.parent.parent.parent
        language_config = package_dir / "assets" / "languages.yml"

        analyzer = Analyzer(
            name=f"{Path.cwd()}/{target_dir.name}",
            path=target_dir,
            language_map_path=language_config,
            custom_language_mapping=self.config.language.custom_language_mapping,
            config=self.config,
        )
        metrics = analyzer.analyze(scan_result, timeout_checker)

        # Dependency analysis
        if self.config.dependencies.include_dependencies:
            project_scanner = ProjectScanner(target_dir)
            try:
                project_info = project_scanner.scan()
                if project_info and project_info.dependencies:
                    dep_info = project_info.dependencies

                    # Show conflict warnings if any
                    if dep_info.conflicts:
                        for conflict in dep_info.conflicts:
                            console.print(
                                f"[yellow]Dependency conflict: {conflict}[/yellow]"
                            )

                    # Create new metrics with dependencies (immutable)
                    metrics = replace(metrics, dependencies=dep_info)
            except ValueError as e:
                # Always warn users when dependency analysis fails; show
                # additional details only in verbose mode.
                console.print(
                    Text(
                        "Warning: failed to analyze dependencies — skipping",
                        style="yellow",
                    )
                )
                if self.config.core.verbose:
                    console.print(Text(f"Details: {e}", style="dim"))

        return metrics

    def _format_metrics(self, metrics: Metrics, output_format: str | None) -> str:
        """Format metrics for output.

        Args:
            metrics: Metrics object to format.
            output_format: Desired format type.

        Returns:
            Formatted string output.
        """
        git_info = (
            GitStats.detect_repository(metrics.path, self.config)
            if self.config.git.enabled
            else None
        )
        return Formatter.format(
            metrics,
            output_format,
            git_info=git_info,
            display_config=self.config.display,
            git_config=self.config.git,
        )
