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
from statsvy.data.scan_result import ScanResult
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
        no_css: bool = False,
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
            no_css: When True suppress any embedded CSS in HTML output.

        Raises:
            TimeoutError: If the scan or analysis exceeds the configured
                timeout limit.
        """
        if self.config.core.verbose:
            inspect(self.config)
            console.print("")  # Blank line for readability

        start = perf_counter()

        perf_tracker = self._confirm_and_prepare_profiling()

        resolved_dir = PathResolver.get_target_directory(target_dir)
        combined_ignore = self._combine_ignore_patterns(ignore_patterns)

        self._log_scan_start(resolved_dir, combined_ignore)

        # When performance tracking is running we disable the runtime timeout
        # so profiling is not interrupted. Create and start the timeout
        # checker once and pass it to the helpers below.
        effective_timeout = (
            0 if self._is_profiling_enabled() else self.config.scan.timeout_seconds
        )
        timeout_checker = TimeoutChecker(effective_timeout)
        timeout_checker.start()

        # Delegate the actual runs (I/O/memory/normal) to a helper so this
        # method remains concise and within complexity limits.
        metrics, perf_metrics, io_metrics, cpu_metrics = self._run_profiles(
            resolved_dir, combined_ignore, perf_tracker, timeout_checker
        )

        end = perf_counter()
        console.print(f"Scan completed in {end - start:.2f} seconds")

        # If we collected memory metrics, show combined output (may include
        # I/O stats attached above). Otherwise show any I/O-only metrics.
        if io_metrics:
            console.print(PerformanceMetricsFormatter.format_text(io_metrics))
        if perf_metrics:
            console.print(PerformanceMetricsFormatter.format_text(perf_metrics))
        if cpu_metrics:
            console.print(PerformanceMetricsFormatter.format_text(cpu_metrics))

        formatted = self._format_metrics(metrics, output_format, include_css=not no_css)

        if self.config.storage.auto_save:
            Storage.save(metrics, config=self.config)

        OutputHandler.handle(formatted, output_path, self.config)

    def _maybe_setup_performance_tracker(self) -> PerformanceTracker | None:
        """Prompt user and (optionally) start a PerformanceTracker.

        Returns the running tracker or None when disabled/declined.
        """
        if not (
            self.config.core.performance.track_mem
            or self.config.core.performance.track_io
            or self.config.core.performance.track_cpu
        ):
            return None

        self._print_profiling_warning()

        try:
            proceed = click.confirm("Proceed with performance tracking?", default=False)
        except (EOFError, KeyboardInterrupt, click.Abort):
            proceed = False

        if proceed:
            tracker = PerformanceTracker()
            tracker.start()
            return tracker

        # User declined — disable for this run and continue (update nested
        # PerformanceConfig instead of the removed legacy flag).
        new_perf = replace(
            self.config.core.performance,
            track_mem=False,
            track_io=False,
            track_cpu=False,
        )
        self.config = replace(
            self.config, core=replace(self.config.core, performance=new_perf)
        )
        return None

    def _is_profiling_enabled(self) -> bool:
        """Return True when any performance profiling is enabled."""
        return (
            self.config.core.performance.track_mem
            or self.config.core.performance.track_io
            or self.config.core.performance.track_cpu
        )

    def _print_profiling_warning(self) -> None:
        """Print profiling warning text with track-specific estimates."""
        message = self._build_profiling_warning_message()
        console.print(Text(message, style="yellow"))

    def _build_profiling_warning_message(self) -> str:
        """Build a warning message for enabled profiling tracks."""
        track_mem = self.config.core.performance.track_mem
        track_io = self.config.core.performance.track_io
        track_cpu = self.config.core.performance.track_cpu

        if track_mem and track_io and track_cpu:
            return (
                "Warning: --profile runs three full scans (I/O, memory, CPU).\n"
                "Total runtime is SIGNIFICANTLY increased.\n"
                "Memory profiling can add substantial extra overhead on large "
                "projects."
            )

        lines: list[str] = ["Warning: Performance profiling enabled."]
        if track_io:
            lines.append(
                "- Tracking I/O performance (--track-io): can add extra overhead "
                "(~10% extra runtime)."
            )
        if track_mem:
            lines.append(
                "- Tracking memory performance (--track-mem): is VERY expensive "
                "(~30-50% on small projects, much higher on large projects)."
            )
        if track_cpu:
            lines.append(
                "- Tracking CPU performance (--track-cpu): can add extra overhead "
                "(~15% extra runtime)."
            )

        selected_count = sum((track_io, track_mem, track_cpu))
        if selected_count > 1:
            lines.append(
                "Combined profiling runs multiple full scans, so total runtime "
                "will increase accordingly."
            )

        return "\n".join(lines)

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

    def _perform_io_scan(
        self,
        resolved_dir: Path,
        combined_ignore: tuple[str, ...],
        timeout_checker: TimeoutChecker,
    ) -> tuple[ScanResult, int, PerformanceMetrics]:
        """Perform a scanner-only run and return scan result + I/O stats.

        Returns: (scan_result, bytes_read, io_metrics). The ScanResult is
        returned so callers can reuse the work without scanning twice.
        """
        io_start = perf_counter()
        scanner = Scanner(
            resolved_dir,
            ignore=combined_ignore,
            no_gitignore=not self.config.scan.respect_gitignore,
            config=self.config,
        )
        scan_result = scanner.scan(timeout_checker)
        io_end = perf_counter()

        bytes_read = getattr(scan_result, "bytes_read", 0)
        elapsed_io = max(1e-6, io_end - io_start)
        io_mb_s = (bytes_read / (1024**2)) / elapsed_io
        io_metrics = PerformanceMetrics(
            peak_memory_bytes=0, bytes_read=bytes_read, io_mb_s=io_mb_s
        )
        return scan_result, bytes_read, io_metrics

    def _analyze_scan_result(
        self,
        resolved_dir: Path,
        scan_result: ScanResult,
        timeout_checker: TimeoutChecker,
    ) -> Metrics:
        """Run analysis step given a ScanResult produced by Scanner.

        Keeps analyze-related logic separate to reduce execute() complexity.
        """
        package_dir = Path(__file__).parent.parent.parent.parent
        language_config = package_dir / "assets" / "languages.yml"

        analyzer = Analyzer(
            name=f"{Path.cwd()}/{resolved_dir.name}",
            path=resolved_dir,
            language_map_path=language_config,
            custom_language_mapping=self.config.language.custom_language_mapping,
            config=self.config,
        )
        return analyzer.analyze(scan_result, timeout_checker)

    def _confirm_and_prepare_profiling(self) -> PerformanceTracker | None:
        """Prompt the user once and prepare a PerformanceTracker instance.

        This method only obtains user consent. It returns an *unstarted*
        PerformanceTracker when memory profiling was requested so that the
        tracker can be started later (right before the memory run). This
        ensures the I/O profiling run remains unaffected by tracemalloc.
        """
        profiling_requested = (
            self.config.core.performance.track_mem
            or self.config.core.performance.track_io
            or self.config.core.performance.track_cpu
        )
        if not profiling_requested:
            return None

        self._print_profiling_warning()

        try:
            proceed = click.confirm("Proceed with performance tracking?", default=False)
        except (EOFError, KeyboardInterrupt, click.Abort):
            proceed = False

        if not proceed:
            # Disable profiling for this invocation and continue. Update the
            # nested PerformanceConfig rather than the removed legacy flags.
            new_perf = replace(
                self.config.core.performance,
                track_mem=False,
                track_io=False,
                track_cpu=False,
            )
            self.config = replace(
                self.config, core=replace(self.config.core, performance=new_perf)
            )
            return None

        # Return an unstarted tracker instance when memory profiling is
        # requested; it will be started later only for the memory run.
        if self.config.core.performance.track_mem:
            return PerformanceTracker(track_memory=True, track_cpu=False)

        return None

    def _run_profiles(
        self,
        resolved_dir: Path,
        combined_ignore: tuple[str, ...],
        perf_tracker: PerformanceTracker | None,
        timeout_checker: TimeoutChecker,
    ) -> tuple[
        Metrics,
        PerformanceMetrics | None,
        PerformanceMetrics | None,
        PerformanceMetrics | None,
    ]:
        """Execute the requested profiling runs and return results.

        Returns a tuple: (metrics, perf_metrics, io_metrics, cpu_metrics).
        """
        io_metrics: PerformanceMetrics | None = None
        perf_metrics: PerformanceMetrics | None = None
        cpu_metrics: PerformanceMetrics | None = None
        metrics: Metrics | None = None

        if self.config.core.performance.track_io:
            # I/O profiling run
            scan_result, bytes_read, io_metrics = self._perform_io_scan(
                resolved_dir, combined_ignore, timeout_checker
            )
            metrics = self._analyze_scan_result(
                resolved_dir, scan_result, timeout_checker
            )
            io_metrics = replace(io_metrics, bytes_read=bytes_read)

        if self.config.core.performance.track_mem:
            # Memory profiling run
            if perf_tracker is None:
                perf_tracker = PerformanceTracker(track_memory=True, track_cpu=False)
            if not perf_tracker.is_active():
                perf_tracker.start()

            metrics = self._run_scan_with_timeout(
                resolved_dir, combined_ignore, timeout_checker, perf_tracker
            )
            perf_metrics = perf_tracker.stop()

        if self.config.core.performance.track_cpu:
            # CPU profiling run
            cpu_tracker = PerformanceTracker(track_memory=False, track_cpu=True)
            cpu_tracker.start()
            metrics = self._run_scan_with_timeout(
                resolved_dir, combined_ignore, timeout_checker, cpu_tracker
            )
            cpu_metrics = cpu_tracker.stop()

        if metrics is None:
            # Plain scan with no profiling
            metrics = self._run_scan_with_timeout(
                resolved_dir, combined_ignore, timeout_checker, perf_tracker
            )

        return metrics, perf_metrics, io_metrics, cpu_metrics

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

    def _format_metrics(
        self,
        metrics: Metrics,
        output_format: str | None,
        include_css: bool | None = None,
    ) -> str:
        """Format metrics for output.

        Args:
            metrics: Metrics object to format.
            output_format: Desired format type.
            include_css: When formatting HTML, whether to embed CSS. ``None``
                defers to the Formatter default (which is True).

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
            include_css=include_css,
        )
