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

from statsvy.data.comparison_config import ComparisonConfig
from statsvy.data.core_config import CoreConfig
from statsvy.data.dependencies_config import DependenciesConfig
from statsvy.data.display_config import DisplayConfig
from statsvy.data.files_config import FilesConfig
from statsvy.data.git_config import GitConfig
from statsvy.data.language_config import LanguageConfig
from statsvy.data.performance_config import PerformanceConfig
from statsvy.data.scan_config import ScanConfig
from statsvy.data.storage_config import StorageConfig


def _mapping_proxy(data: Mapping[str, Any] | None) -> Mapping[str, Any]:
    """Return an immutable mapping proxy for configuration values.

    Args:
        data: Input mapping to wrap.

    Returns:
        An immutable mapping proxy.
    """
    return MappingProxyType(dict(data or {}))


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


__all__ = [
    "ComparisonConfig",
    "Config",
    "CoreConfig",
    "DependenciesConfig",
    "DisplayConfig",
    "FilesConfig",
    "GitConfig",
    "LanguageConfig",
    "PerformanceConfig",
    "ScanConfig",
    "StorageConfig",
]
