"""Mapping utilities between internal models and public API DTOs."""

from datetime import datetime
from pathlib import Path

from statsvy.api.api_comparison_result import ApiComparisonResult
from statsvy.api.api_scan_result import ApiScanResult
from statsvy.data.comparison_result import ComparisonResult
from statsvy.data.dependency import Dependency
from statsvy.data.dependency_info import DependencyInfo
from statsvy.data.metrics import Metrics


class ApiMapper:
    """Maps between internal domain models and public API DTOs."""

    @staticmethod
    def to_api_scan_result(metrics: Metrics) -> ApiScanResult:
        """Convert internal ``Metrics`` into ``ApiScanResult``.

        Args:
            metrics: Internal metrics object.

        Returns:
            Public API DTO.
        """
        dependency_info = metrics.dependencies
        dependencies: tuple[tuple[str, str, str, str], ...] = ()
        dependency_total: int | None = None
        dependency_prod: int | None = None
        dependency_dev: int | None = None
        dependency_optional: int | None = None
        dependency_sources: tuple[str, ...] = ()
        dependency_conflicts: tuple[str, ...] = ()

        if dependency_info is not None:
            dependencies = tuple(
                (
                    dependency.name,
                    dependency.version,
                    dependency.category,
                    dependency.source_file,
                )
                for dependency in dependency_info.dependencies
            )
            dependency_total = dependency_info.total_count
            dependency_prod = dependency_info.prod_count
            dependency_dev = dependency_info.dev_count
            dependency_optional = dependency_info.optional_count
            dependency_sources = dependency_info.sources
            dependency_conflicts = dependency_info.conflicts

        return ApiScanResult(
            name=metrics.name,
            path=str(metrics.path),
            timestamp=metrics.timestamp.isoformat(),
            total_files=metrics.total_files,
            total_size_bytes=metrics.total_size_bytes,
            total_size_kb=metrics.total_size_kb,
            total_size_mb=metrics.total_size_mb,
            total_lines=metrics.total_lines,
            lines_by_lang=dict(metrics.lines_by_lang),
            comment_lines_by_lang=dict(metrics.comment_lines_by_lang),
            blank_lines_by_lang=dict(metrics.blank_lines_by_lang),
            lines_by_category=dict(metrics.lines_by_category),
            comment_lines=metrics.comment_lines,
            blank_lines=metrics.blank_lines,
            dependency_total=dependency_total,
            dependency_prod=dependency_prod,
            dependency_dev=dependency_dev,
            dependency_optional=dependency_optional,
            dependency_sources=dependency_sources,
            dependency_conflicts=dependency_conflicts,
            dependencies=dependencies,
        )

    @staticmethod
    def to_api_comparison_result(comparison: ComparisonResult) -> ApiComparisonResult:
        """Convert internal ``ComparisonResult`` to ``ApiComparisonResult``.

        Args:
            comparison: Internal comparison object.

        Returns:
            Public API DTO.
        """
        return ApiComparisonResult(
            project1=ApiMapper.to_api_scan_result(comparison.project1),
            project2=ApiMapper.to_api_scan_result(comparison.project2),
            deltas=dict(comparison.deltas),
            timestamp=comparison.timestamp.isoformat(),
        )

    @staticmethod
    def to_internal_metrics(result: ApiScanResult) -> Metrics:
        """Convert ``ApiScanResult`` to internal ``Metrics``.

        Args:
            result: Public API scan DTO.

        Returns:
            Internal metrics object.
        """
        dependency_info = ApiMapper._to_dependency_info(result)

        return Metrics(
            name=result.name,
            path=Path(result.path),
            timestamp=datetime.fromisoformat(result.timestamp),
            total_files=result.total_files,
            total_size_bytes=result.total_size_bytes,
            total_size_kb=result.total_size_kb,
            total_size_mb=result.total_size_mb,
            lines_by_lang=dict(result.lines_by_lang),
            comment_lines_by_lang=dict(result.comment_lines_by_lang),
            blank_lines_by_lang=dict(result.blank_lines_by_lang),
            lines_by_category=dict(result.lines_by_category),
            comment_lines=result.comment_lines,
            blank_lines=result.blank_lines,
            total_lines=result.total_lines,
            dependencies=dependency_info,
        )

    @staticmethod
    def to_internal_comparison(result: ApiComparisonResult) -> ComparisonResult:
        """Convert ``ApiComparisonResult`` to internal ``ComparisonResult``.

        Args:
            result: Public API comparison DTO.

        Returns:
            Internal comparison object.
        """
        return ComparisonResult(
            project1=ApiMapper.to_internal_metrics(result.project1),
            project2=ApiMapper.to_internal_metrics(result.project2),
            deltas=dict(result.deltas),
            timestamp=datetime.fromisoformat(result.timestamp),
        )

    @staticmethod
    def _to_dependency_info(result: ApiScanResult) -> DependencyInfo | None:
        """Build internal dependency info from API DTO.

        Args:
            result: API scan result.

        Returns:
            DependencyInfo when dependency fields are present, otherwise None.
        """
        has_dependency_payload = (
            result.dependency_total is not None
            or result.dependency_prod is not None
            or result.dependency_dev is not None
            or result.dependency_optional is not None
            or bool(result.dependencies)
        )
        if not has_dependency_payload:
            return None

        dependencies = tuple(
            Dependency(
                name=name,
                version=version,
                category=category,
                source_file=source_file,
            )
            for name, version, category, source_file in result.dependencies
        )

        return DependencyInfo(
            dependencies=dependencies,
            prod_count=result.dependency_prod or 0,
            dev_count=result.dependency_dev or 0,
            optional_count=result.dependency_optional or 0,
            total_count=result.dependency_total or len(dependencies),
            sources=result.dependency_sources,
            conflicts=result.dependency_conflicts,
        )
