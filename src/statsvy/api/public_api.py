"""Public API facade for programmatic Statsvy usage."""

from dataclasses import replace
from pathlib import Path

from statsvy.api.api_comparison_result import ApiComparisonResult
from statsvy.api.api_mapper import ApiMapper
from statsvy.api.api_scan_result import ApiScanResult
from statsvy.core.analyzer import Analyzer
from statsvy.core.comparison import ComparisonAnalyzer
from statsvy.core.formatter import Formatter
from statsvy.core.git_stats import GitStats
from statsvy.core.project_scanner import ProjectScanner
from statsvy.core.scanner import Scanner
from statsvy.data.config import Config
from statsvy.data.metrics import Metrics
from statsvy.utils.timeout_checker import TimeoutChecker


class StatsvyApi:
    """Class-based public API facade for Statsvy integrations."""

    @staticmethod
    def scan(path: str | Path, config: Config | None = None) -> ApiScanResult:
        """Scan and analyze a directory.

        Args:
            path: Target directory to scan.
            config: Optional configuration overrides.

        Returns:
            API DTO containing scan and analysis metrics.

        Raises:
            ValueError: If ``path`` does not exist or is not a directory.
            TimeoutError: If scan or analysis exceeds configured timeout.
        """
        effective_config = config or Config.default()
        target_path = Path(path)
        timeout_checker = TimeoutChecker(effective_config.scan.timeout_seconds)
        timeout_checker.start()

        scanner = Scanner(
            target_path,
            ignore=effective_config.scan.ignore_patterns,
            no_gitignore=not effective_config.scan.respect_gitignore,
            config=effective_config,
        )
        scan_result = scanner.scan(timeout_checker)

        analyzer = Analyzer(
            name=f"{Path.cwd()}/{target_path.name}",
            path=target_path,
            language_map_path=StatsvyApi._language_config_path(),
            custom_language_mapping=effective_config.language.custom_language_mapping,
            config=effective_config,
        )
        metrics = analyzer.analyze(scan_result, timeout_checker)
        metrics_with_dependencies = StatsvyApi._attach_dependencies(
            metrics, target_path, effective_config
        )
        return ApiMapper.to_api_scan_result(metrics_with_dependencies)

    @staticmethod
    def compare(
        project1: ApiScanResult,
        project2: ApiScanResult,
    ) -> ApiComparisonResult:
        """Compare two API scan snapshots.

        Args:
            project1: First project scan result.
            project2: Second project scan result.

        Returns:
            API DTO containing computed deltas.
        """
        project1_metrics = ApiMapper.to_internal_metrics(project1)
        project2_metrics = ApiMapper.to_internal_metrics(project2)
        comparison = ComparisonAnalyzer.compare(project1_metrics, project2_metrics)
        return ApiMapper.to_api_comparison_result(comparison)

    @staticmethod
    def format_result(
        result: ApiScanResult | ApiComparisonResult,
        output_format: str | None = None,
        config: Config | None = None,
        include_css: bool | None = None,
    ) -> str:
        """Format API DTO results into text output.

        Args:
            result: API scan or comparison DTO to format.
            output_format: Output format (``table``, ``json``, ``markdown``,
                ``md``, ``html``). Uses config default when omitted.
            config: Optional configuration controlling formatter behavior.
            include_css: When using HTML, controls embedded CSS output.

        Returns:
            Formatted output text.

        Raises:
            ValueError: If output format is unknown.
        """
        effective_config = config or Config.default()
        selected_format = output_format or effective_config.core.default_format

        if isinstance(result, ApiComparisonResult):
            internal_comparison = ApiMapper.to_internal_comparison(result)
            return Formatter.format(
                internal_comparison,
                selected_format,
                display_config=effective_config.display,
                include_css=include_css,
            )

        internal_metrics = ApiMapper.to_internal_metrics(result)
        git_info = (
            GitStats.detect_repository(internal_metrics.path, effective_config)
            if effective_config.git.enabled
            else None
        )
        return Formatter.format(
            internal_metrics,
            selected_format,
            git_info=git_info,
            display_config=effective_config.display,
            git_config=effective_config.git,
            include_css=include_css,
        )

    @staticmethod
    def _language_config_path() -> Path:
        """Return path to built-in language mapping asset."""
        package_dir = Path(__file__).resolve().parent.parent.parent.parent
        return package_dir / "assets" / "languages.yml"

    @staticmethod
    def _attach_dependencies(
        metrics: Metrics,
        target_path: Path,
        config: Config,
    ) -> Metrics:
        """Attach dependency analysis data when enabled.

        Dependency analysis failures are treated as non-fatal and the original
        metrics are returned unchanged.
        """
        if not config.dependencies.include_dependencies:
            return metrics

        project_scanner = ProjectScanner(target_path)
        try:
            project_info = project_scanner.scan()
        except ValueError:
            return metrics

        if project_info is None or project_info.dependencies is None:
            return metrics

        return replace(metrics, dependencies=project_info.dependencies)
