"""Analysis workflow for scanned file results."""

from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any

from rich.columns import Columns
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.text import Text

from statsvy.data.config import Config
from statsvy.data.metrics import Metrics
from statsvy.data.scan_result import ScanResult
from statsvy.language_parsing.language_analyzer import LanguageAnalyzer
from statsvy.language_parsing.language_detector import LanguageDetector
from statsvy.utils.console import console
from statsvy.utils.timeout_checker import TimeoutChecker


class Analyzer:
    """Analyzes directory scan results to generate detailed code metrics.

    This class processes file contents to calculate total line counts and
    distribution of code across different programming languages. Language
    detection is delegated to a LanguageDetector instance.

    Attributes:
        name (str): The name of the analysis project or session.
        path (Path): The root directory path being analyzed.
        language_detector (LanguageDetector): Instance for detecting file
            programming languages.
    """

    def __init__(
        self,
        name: str,
        path: Path,
        language_map_path: Path | None = None,
        custom_language_mapping: Mapping[str, Any] | None = None,
        config: Config | None = None,
    ) -> None:
        """Initialize the Analyzer.

        Detailed setup of the analyzer with a project name, target path
        and optional language configuration.

        Args:
            name (str): The identifier for the analysis.
            path (Path): The filesystem path to the directory being analyzed.
            language_map_path (Path | None): Path to a YAML file containing
                language configuration mappings. If provided, the file should
                contain language names as keys with "extensions" and "filenames"
                lists as values. If None or file doesn't exist, all files are
                marked as "unknown" language. Defaults to None.
            custom_language_mapping (Mapping[str, Any] | None): Optional mapping
                that extends or overrides entries in the YAML configuration.
                Custom mappings win on conflicts. Defaults to None.
            config (Config | None): Optional configuration for analysis settings.

        Raises:
            ValueError: If language_map_path is provided but contains invalid
                YAML syntax or cannot be read.
        """
        self.name = name
        self.path = path
        self.config = config or Config.default()
        self.language_detector = LanguageDetector(
            language_map_path,
            custom_language_mapping=custom_language_mapping,
        )
        self.language_analyzer = LanguageAnalyzer(self.config)
        if self.config.core.verbose:
            console.print("Initialized Analyzer")

    def analyze(
        self, scan_result: ScanResult, timeout_checker: TimeoutChecker | None = None
    ) -> Metrics:
        """Processes a list of files to compile comprehensive metrics.

        Iterates through the provided files, counts lines of code, and
        categorizes them by their programming language. Language detection
        is performed using the LanguageDetector.

        Args:
            scan_result (ScanResult): Metadata from the initial directory scan
                including file paths to analyze, total file count, and total
                size in bytes.
            timeout_checker: Optional timeout checker to enforce analysis time limits.

        Returns:
            Metrics: A data object containing calculated statistics including:
                - total_lines: Sum of all lines across all files
                - lines_by_lang: Dictionary mapping language names
                    to line counts
                - total_size_kb and total_size_mb: Size in different units
                - timestamp: When the analysis was performed

        Raises:
            TimeoutError: If timeout_checker detects timeout exceeded.
        """
        if self.config.core.verbose:
            console.print("Start analyzing...")

        metrics_data = self._initialize_metrics_data()
        show_progress = self.config.core.show_progress

        # Exclude duplicate files from analysis (duplicates detected during scan)
        files_to_analyze = tuple(
            f
            for f in scan_result.scanned_files
            if f not in getattr(scan_result, "duplicate_files", ())
        )

        # Provide optional per-file metadata (from Scanner) to avoid
        # reopening files during analysis. If absent, Analyzer falls back
        # to the previous behavior and will read files directly.
        file_data_map = getattr(scan_result, "file_data", None)

        if show_progress:
            self._analyze_with_progress(
                files_to_analyze, metrics_data, timeout_checker, file_data_map
            )
        else:
            self._analyze_without_progress(
                files_to_analyze, metrics_data, timeout_checker, file_data_map
            )

        if self.config.core.verbose:
            self._log_analysis_summary(metrics_data)

        return self._create_metrics(scan_result, metrics_data)

    @staticmethod
    def _initialize_metrics_data() -> dict[str, Any]:
        """Initialize empty metrics data structure.

        Returns:
            Dictionary with zeroed counters and empty language mappings.
        """
        return {
            "total_lines": 0,
            "lines_by_lang": {},
            "lines_by_category": {},
            "comment_lines": 0,
            "blank_lines": 0,
            "comment_lines_by_lang": {},
            "blank_lines_by_lang": {},
        }

    def _analyze_with_progress(
        self,
        files: tuple[Path, ...],
        metrics_data: dict[str, Any],
        timeout_checker: TimeoutChecker | None,
        file_data_map: dict[Path, dict[str, object]] | None = None,
    ) -> None:
        """Analyze files with progress bar display.

        Args:
            files: File paths to analyze.
            metrics_data: Mutable metrics accumulator to update.
            timeout_checker: Optional timeout checker to enforce analysis time limits.
            file_data_map: Optional mapping of Path -> precomputed file metadata.

        Raises:
            TimeoutError: If timeout_checker detects timeout exceeded.
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[green]Analyzing files...", total=len(files))

            for file in files:
                if timeout_checker:
                    timeout_checker.check("file analysis")
                progress.update(task, advance=1)
                if file.is_file():
                    self._process_file(file, metrics_data, file_data_map)

    def _analyze_without_progress(
        self,
        files: tuple[Path, ...],
        metrics_data: dict[str, Any],
        timeout_checker: TimeoutChecker | None,
        file_data_map: dict[Path, dict[str, object]] | None = None,
    ) -> None:
        """Analyze files without progress bar display.

        Args:
            files: File paths to analyze.
            metrics_data: Mutable metrics accumulator to update.
            timeout_checker: Optional timeout checker to enforce analysis time limits.
            file_data_map: Optional mapping of Path -> precomputed file metadata.

        Raises:
            TimeoutError: If timeout_checker detects timeout exceeded.
        """
        for file in files:
            if timeout_checker:
                timeout_checker.check("file analysis")
            if file.is_file():
                self._process_file(file, metrics_data, file_data_map)

    def _get_text_and_line_count(
        self, file: Path, file_info: dict[str, object] | None
    ) -> tuple[str, int]:
        """Return (text, line_count) for a file using optional precomputed info.

        This centralizes text/line retrieval and keeps _process_file simple.
        """
        if file_info is not None:
            # Prefer already-read string values
            text_val = file_info.get("text")
            if isinstance(text_val, str):
                lines_val = file_info.get("lines")
                lines = int(lines_val) if isinstance(lines_val, int) else 0
                return text_val, lines

            # If only bytes available, decode once
            b_val = file_info.get("bytes")
            if isinstance(b_val, bytes | bytearray):
                decoded = b_val.decode("utf-8", errors="ignore")
                return decoded, len(decoded.splitlines())

        # Fallback: read from filesystem
        text = file.read_text(encoding="utf-8", errors="ignore")
        return text, len(text.splitlines())

    def _process_file(
        self,
        file: Path,
        metrics_data: dict[str, Any],
        file_data_map: dict[Path, dict[str, object]] | None = None,
    ) -> None:
        """Process a single file and update metrics data.

        Uses optional precomputed file metadata from `file_data_map` when
        available to avoid reopening files. Falls back to the previous
        behavior when metadata is not present.
        """
        file_info = file_data_map.get(file) if file_data_map else None

        # Skip binary files (prefer scan-provided info, else use extension)
        if file_info is not None and file_info.get("is_binary"):
            return
        if file_info is None and self._is_binary_file(file):
            return

        text, lines = self._get_text_and_line_count(file, file_info)

        # Skip files that don't meet minimum lines threshold
        if lines < self.config.language.min_lines_threshold:
            return

        lang = self.language_detector.detect(file)
        category = self.language_detector.get_category(lang)

        comments, blanks = self.language_analyzer.analyze(file, text)

        file_stats = {"lines": lines, "comments": comments, "blanks": blanks}

        self._update_metrics(metrics_data, lang, category, file_stats)

        if self.config.core.verbose:
            self._log_file_analysis(file, category, lang)

    def _update_metrics(
        self,
        metrics_data: dict[str, Any],
        lang: str,
        category: str,
        stats: dict[str, int],
    ) -> None:
        """Update metrics data with file statistics.

        Args:
            metrics_data: Mutable metrics accumulator to update.
            lang: Detected language name for the file.
            category: Detected language category for the file.
            stats: Per-file statistics (lines, comments, blanks).
        """
        metrics_data["lines_by_lang"][lang] = (
            metrics_data["lines_by_lang"].get(lang, 0) + stats["lines"]
        )
        metrics_data["lines_by_category"][category] = (
            metrics_data["lines_by_category"].get(category, 0) + stats["lines"]
        )

        metrics_data["total_lines"] += stats["lines"]
        metrics_data["comment_lines"] += stats["comments"]
        metrics_data["blank_lines"] += stats["blanks"]

        metrics_data["comment_lines_by_lang"][lang] = (
            metrics_data["comment_lines_by_lang"].get(lang, 0) + stats["comments"]
        )
        metrics_data["blank_lines_by_lang"][lang] = (
            metrics_data["blank_lines_by_lang"].get(lang, 0) + stats["blanks"]
        )

    @staticmethod
    def _count_file_lines(file: Path) -> int:
        """Count total lines in a file.

        Args:
            file: File path to count lines for.

        Returns:
            Total number of lines in the file.
        """
        with file.open("r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)

    def _is_binary_file(self, file: Path) -> bool:
        """Check if a file is binary based on its extension.

        Args:
            file: File path to check.

        Returns:
            True if file has a binary extension, False otherwise.
        """
        return file.suffix.lower() in self.config.scan.binary_extensions

    @staticmethod
    def _log_file_analysis(file: Path, category: str, lang: str) -> None:
        """Log file analysis details in verbose mode.

        Args:
            file: File path being analyzed.
            category: Detected language category for the file.
            lang: Detected language name for the file.
        """
        file_renderable = Text(str(file), overflow="ellipsis")
        cat_renderable = Text(category, style="magenta")
        lang_renderable = Text(lang, style="cyan")

        console.print(Columns([file_renderable, cat_renderable, lang_renderable]))

    def _create_metrics(
        self, scan_result: ScanResult, metrics_data: dict[str, Any]
    ) -> Metrics:
        """Create Metrics object from collected data.

        Args:
            scan_result: Scan metadata including file list and size totals.
            metrics_data: Aggregated metrics from analysis.

        Returns:
            Metrics object with aggregated analysis results.
        """
        return Metrics(
            name=self.name,
            path=self.path,
            timestamp=datetime.now(),
            total_files=scan_result.total_files,
            total_size_bytes=scan_result.total_size_bytes,
            total_size_kb=scan_result.total_size_bytes // 1024,
            total_size_mb=scan_result.total_size_bytes // (1024 * 1024),
            lines_by_lang=MappingProxyType(dict(metrics_data["lines_by_lang"])),
            comment_lines_by_lang=MappingProxyType(
                dict(metrics_data["comment_lines_by_lang"])
            ),
            blank_lines_by_lang=MappingProxyType(
                dict(metrics_data["blank_lines_by_lang"])
            ),
            lines_by_category=MappingProxyType(dict(metrics_data["lines_by_category"])),
            comment_lines=metrics_data["comment_lines"],
            blank_lines=metrics_data["blank_lines"],
            total_lines=metrics_data["total_lines"],
        )

    @staticmethod
    def _log_analysis_summary(metrics_data: dict[str, Any]) -> None:
        """Log analysis summary in verbose mode.

        Args:
            metrics_data: Aggregated metrics from analysis.
        """
        console.print("\nAnalysis summary:")
        console.print(
            Text("Total lines: ") + Text(f"{metrics_data['total_lines']}", style="cyan")
        )
        console.print(
            Text("Comment lines: ")
            + Text(f"{metrics_data['comment_lines']}", style="cyan")
        )
        console.print(
            Text("Blank lines: ") + Text(f"{metrics_data['blank_lines']}", style="cyan")
        )

        if metrics_data["lines_by_lang"]:
            console.print("\nLines by language:")
            for lang, lines in sorted(
                metrics_data["lines_by_lang"].items(), key=lambda x: x[1], reverse=True
            )[:10]:  # Show top 10
                console.print(
                    Text(f"  {lang}: ", style="dim") + Text(f"{lines}", style="cyan")
                )
