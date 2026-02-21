"""Configuration module for the Statsvy application.

This module defines immutable configuration structures for the application.
Defaults are provided via the ``Config.default()`` factory and can be
overridden by ConfigLoader using explicit updates.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any


def _mapping_proxy(data: Mapping[str, Any] | None) -> Mapping[str, Any]:
    """Return an immutable mapping proxy for configuration values.

    Args:
        data: Input mapping to wrap.

    Returns:
        An immutable mapping proxy.
    """
    return MappingProxyType(dict(data or {}))


@dataclass(frozen=True, slots=True)
class PerformanceConfig:
    """Performance-related flags grouped together.

    - track_mem: measure memory (tracemalloc)
    - track_io: measure I/O throughput (MB/s)
    - track_cpu: measure process CPU usage (without psutil)
    """

    track_mem: bool
    track_io: bool
    track_cpu: bool


@dataclass(frozen=True, slots=True)
class CoreConfig:
    """Core application settings."""

    name: str
    path: str
    default_format: str
    out_dir: str
    verbose: bool
    color: bool
    show_progress: bool
    performance: PerformanceConfig


@dataclass(frozen=True, slots=True)
class ScanConfig:
    """File system scanning settings.

    Attributes:
        min_file_size_mb: Minimum file size (in MB) to include in the scan.
            Files smaller than this will be skipped when scanning.
    """

    follow_symlinks: bool
    max_depth: int
    min_file_size_mb: float
    max_file_size_mb: float
    respect_gitignore: bool
    include_hidden: bool
    timeout_seconds: int
    ignore_patterns: tuple[str, ...]
    binary_extensions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LanguageConfig:
    """Language detection and line-counting settings."""

    custom_language_mapping: Mapping[str, Any]
    exclude_languages: tuple[str, ...]
    min_lines_threshold: int
    count_comments: bool
    count_blank_lines: bool
    count_docstrings: bool


@dataclass(frozen=True, slots=True)
class StorageConfig:
    """Persistence settings."""

    auto_save: bool


@dataclass(frozen=True, slots=True)
class GitConfig:
    """Git integration settings."""

    enabled: bool
    include_stats: bool
    include_branches: tuple[str, ...]
    detect_authors: bool
    show_contributors: bool
    max_contributors: int


@dataclass(frozen=True, slots=True)
class DisplayConfig:
    """Terminal display preferences."""

    truncate_paths: bool
    show_percentages: bool
    show_deps_list: bool = True


@dataclass(frozen=True, slots=True)
class ComparisonConfig:
    """Comparison and delta settings."""

    show_unchanged: bool


@dataclass(frozen=True, slots=True)
class DependenciesConfig:
    """Dependency analysis settings.

    Attributes:
        include_dependencies: Whether to analyze dependencies (default True).
        exclude_dev_dependencies: Whether to exclude dev dependencies from analysis.
    """

    include_dependencies: bool = True
    exclude_dev_dependencies: bool = False


@dataclass(frozen=True, slots=True)
class FilesConfig:
    """File-level analysis settings.

    Duplicate detection is now a core behaviour and cannot be disabled.
    The configuration keeps only the threshold for when to compute hashes.
    """

    duplicate_threshold_bytes: int
    find_large_files: bool
    large_file_threshold_mb: int


@dataclass(frozen=True, slots=True)
class Config:
    """Immutable configuration registry for Statsvy.

    Attributes:
        core: General application settings (verbosity, output, formats).
        scan: File system scanning parameters (depth, ignores, limits).
        language: Language detection and line-counting logic.
        storage: Data persistence settings.
        git: Git integration and repository analysis settings.
        display: Visual formatting for terminal output (themes, tables).
        reporting: Settings for generating external reports (Markdown/HTML).
        comparison: Logic for comparing metrics over time.
        dependencies: Dependency analysis configuration.
        files: File-level analysis (duplicates, large files).
        projects: Project-specific metadata.
    """

    core: CoreConfig
    scan: ScanConfig
    language: LanguageConfig
    storage: StorageConfig
    git: GitConfig
    display: DisplayConfig
    comparison: ComparisonConfig
    dependencies: DependenciesConfig
    files: FilesConfig

    @staticmethod
    def default() -> "Config":
        """Return a Config instance with default settings.

        Returns:
            A Config instance populated with default values.
        """
        return Config(
            core=CoreConfig(
                name="statsvy-projekt",
                path=str(Path.cwd()),
                default_format="table",
                out_dir="./",
                verbose=False,
                color=True,
                show_progress=True,
                performance=PerformanceConfig(
                    track_mem=False,
                    track_io=False,
                    track_cpu=False,
                ),
            ),
            scan=ScanConfig(
                follow_symlinks=False,
                max_depth=-1,
                min_file_size_mb=0.0,
                max_file_size_mb=100.0,
                respect_gitignore=True,
                include_hidden=False,
                timeout_seconds=300,
                ignore_patterns=(".git",),
                binary_extensions=(
                    ".exe",
                    ".dll",
                    ".so",
                    ".dylib",
                    ".jpg",
                    ".png",
                    ".gif",
                    ".pdf",
                    ".zip",
                    ".tar",
                    ".gz",
                    ".pyc",
                ),
            ),
            language=LanguageConfig(
                custom_language_mapping=_mapping_proxy({}),
                exclude_languages=(),
                min_lines_threshold=0,
                count_comments=True,
                count_blank_lines=True,
                count_docstrings=True,
            ),
            storage=StorageConfig(
                auto_save=True,
            ),
            git=GitConfig(
                enabled=True,
                include_stats=True,
                include_branches=(),
                detect_authors=True,
                show_contributors=True,
                max_contributors=5,
            ),
            display=DisplayConfig(
                truncate_paths=True,
                show_percentages=True,
                show_deps_list=True,
            ),
            comparison=ComparisonConfig(
                show_unchanged=False,
            ),
            dependencies=DependenciesConfig(
                include_dependencies=True,
                exclude_dev_dependencies=False,
            ),
            files=FilesConfig(
                duplicate_threshold_bytes=1024,
                find_large_files=True,
                large_file_threshold_mb=10,
            ),
        )
