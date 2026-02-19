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
from statsvy.data.performance_metrics import PerformanceMetrics
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

        proceed = self._maybe_setup_performance_tracker()

        resolved_dir = PathResolver.get_target_directory(target_dir)
        combined_ignore = self._combine_ignore_patterns(ignore_patterns)

        self._log_scan_start(resolved_dir, combined_ignore)

        # Disable runtime timeout while profiling to avoid interruptions
        effective_timeout = 0 if proceed else self.config.scan.timeout_seconds
        timeout_checker = TimeoutChecker(effective_timeout)
        timeout_checker.start()

        metrics: Metrics | None = None
        perf_metrics = None

        # Profiling and non-profiling execution paths are handled by a
        # helper to keep this method concise for linting and testing.
        if proceed and (
            self.config.core.track_io
            or self.config.core.track_mem
            or self.config.core.track_performance
        ):
            metrics, perf_metrics, io_perf_metrics = self._perform_profiling_runs(
                resolved_dir, combined_ignore, timeout_checker
            )
        else:
            # Regular single run (no profiling)
            metrics = self._run_scan_with_timeout(
                resolved_dir, combined_ignore, timeout_checker, None
            )
            perf_metrics = None
            io_perf_metrics = None

        end = perf_counter()
        console.print(f"Scan completed in {end - start:.2f} seconds")

        # Consolidate and print profiling results after all passes complete.
        self._print_performance_metrics(locals().get("io_perf_metrics"), perf_metrics)

        # Finalize output: format, optionally save, and emit to destination.
        self._finalize_output(metrics, output_format, output_path)

    def _print_performance_metrics(
        self,
        io_metrics: PerformanceMetrics | None,
        mem_metrics: PerformanceMetrics | None,
    ) -> None:
        """Print combined or single performance summaries."""
        if io_metrics is None and mem_metrics is None:
            return

        if io_metrics is not None and mem_metrics is not None:
            combined = PerformanceMetrics(
                peak_memory_bytes=mem_metrics.peak_memory_bytes,
                total_bytes_read=io_metrics.total_bytes_read,
                total_io_time_seconds=io_metrics.total_io_time_seconds,
                files_read_count=io_metrics.files_read_count,
            )
            console.print(PerformanceMetricsFormatter.format_text(combined))
            return

        single = io_metrics or mem_metrics
        if single is not None:
            console.print(PerformanceMetricsFormatter.format_text(single))

    def _finalize_output(
        self,
        metrics: Metrics | None,
        output_format: str | None,
        output_path: Path | None,
    ) -> None:
        """Format metrics, optionally save to history, then handle output."""
        formatted = (
            self._format_metrics(metrics, output_format) if metrics is not None else ""
        )

        if self.config.storage.auto_save and metrics is not None:
            Storage.save(metrics, config=self.config)

        OutputHandler.handle(formatted, output_path, self.config)

    def _maybe_setup_performance_tracker(self) -> bool:
        """Prompt the user once when any profiling mode is requested.

        Returns True when the user confirms profiling should proceed. If the
        user declines, the corresponding flags in the configuration are
        disabled for this run.
        """
        if not (
            self.config.core.track_performance
            or self.config.core.track_io
            or self.config.core.track_mem
        ):
            return False

        console.print(
            Text(
                "Warning: enabling profiling will significantly slow the scan "
                "and may increase memory usage. This is intended for development.",
                style="yellow",
            )
        )

        try:
            proceed = click.confirm("Proceed with profiling?", default=False)
        except (EOFError, KeyboardInterrupt, click.Abort):
            proceed = False

        if not proceed:
            # Disable profiling flags for this run
            self.config = replace(
                self.config,
                core=replace(
                    self.config.core,
                    track_performance=False,
                    track_io=False,
                    track_mem=False,
                ),
            )

        return proceed

    def _perform_profiling_runs(
        self,
        resolved_dir: Path,
        combined_ignore: tuple[str, ...],
        timeout_checker: TimeoutChecker,
    ) -> tuple[Metrics | None, PerformanceMetrics | None, PerformanceMetrics | None]:
        """Execute requested profiling passes and return results.

        Returns a tuple of (metrics, perf_metrics, io_perf_metrics). For the
        dual-pass (I/O then memory) case both `io_perf_metrics` and
        `perf_metrics` are populated; for single-pass cases the other value
        will be None.
        """
        io_perf_metrics: PerformanceMetrics | None = None

        if self.config.core.track_io and self.config.core.track_mem:
            # Dual-pass: run I/O pass first (metrics not persisted), then memory
            _, io_perf_metrics = self._run_io_pass(
                resolved_dir, combined_ignore, timeout_checker
            )
            metrics, perf_metrics = self._run_mem_pass(
                resolved_dir, combined_ignore, timeout_checker
            )

        elif self.config.core.track_io:
            # Single I/O pass
            metrics, perf_metrics = self._run_io_pass(
                resolved_dir, combined_ignore, timeout_checker
            )

        else:
            # Memory-only pass
            metrics, perf_metrics = self._run_mem_pass(
                resolved_dir, combined_ignore, timeout_checker
            )

        return metrics, perf_metrics, io_perf_metrics

    def _run_io_pass(
        self,
        resolved_dir: Path,
        combined_ignore: tuple[str, ...],
        timeout_checker: TimeoutChecker,
    ) -> tuple[Metrics | None, PerformanceMetrics | None]:
        """Run a single I/O profiling pass and return (metrics, perf_metrics)."""
        console.print("Running I/O profiling...")
        tracker = PerformanceTracker(track_memory=False, track_io=True)
        tracker.start()
        try:
            metrics = self._run_scan_with_timeout(
                resolved_dir, combined_ignore, timeout_checker, tracker
            )
        finally:
            perf_metrics = tracker.stop()
        return metrics, perf_metrics

    def _run_mem_pass(
        self,
        resolved_dir: Path,
        combined_ignore: tuple[str, ...],
        timeout_checker: TimeoutChecker,
    ) -> tuple[Metrics | None, PerformanceMetrics | None]:
        """Run a single memory profiling pass and return (metrics, perf_metrics)."""
        console.print("Running memory profiling...")
        tracker = PerformanceTracker(track_memory=True, track_io=False)
        tracker.start()
        try:
            metrics = self._run_scan_with_timeout(
                resolved_dir, combined_ignore, timeout_checker, tracker
            )
        finally:
            perf_metrics = tracker.stop()
        return metrics, perf_metrics

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
                resolved_dir, combined_ignore, timeout_checker, perf_tracker
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
        perf_tracker: PerformanceTracker | None = None,
    ) -> Metrics:
        """Perform directory scan and file analysis.

        Args:
            target_dir: Directory to scan.
            ignore_patterns: Patterns to exclude.
            timeout_checker: Timeout checker to enforce time limits.
            perf_tracker: Optional PerformanceTracker injected for instrumentation.

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
            perf_tracker=perf_tracker,
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
            perf_tracker=perf_tracker,
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
