"""Public DTO for scan results.

This data structure is part of the programmatic API contract and is intended
to be stable across patch/minor releases within the same major version.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApiScanResult:
    """Represent an API-safe scan result contract.

    Attributes:
        name: Project or scan run identifier.
        path: Filesystem path that was analyzed.
        timestamp: ISO-8601 timestamp when the scan completed.
        total_files: Number of scanned files.
        total_size_bytes: Total size in bytes for scanned files.
        total_size_kb: Total size in kilobytes.
        total_size_mb: Total size in megabytes.
        total_lines: Total number of analyzed lines.
        lines_by_lang: Line counts per language.
        comment_lines_by_lang: Comment line counts per language.
        blank_lines_by_lang: Blank line counts per language.
        lines_by_category: Line counts grouped by category.
        comment_lines: Total comment lines.
        blank_lines: Total blank lines.
        dependency_total: Total number of detected dependencies.
        dependency_prod: Number of production dependencies.
        dependency_dev: Number of development dependencies.
        dependency_optional: Number of optional dependencies.
        dependency_sources: Source files used for dependency analysis.
        dependency_conflicts: Reported dependency conflicts.
        dependencies: Dependency tuples as
            ``(name, version, category, source_file)``.
    """

    name: str
    path: str
    timestamp: str
    total_files: int
    total_size_bytes: int
    total_size_kb: int
    total_size_mb: int
    total_lines: int
    lines_by_lang: dict[str, int]
    comment_lines_by_lang: dict[str, int]
    blank_lines_by_lang: dict[str, int]
    lines_by_category: dict[str, int]
    comment_lines: int
    blank_lines: int
    dependency_total: int | None = None
    dependency_prod: int | None = None
    dependency_dev: int | None = None
    dependency_optional: int | None = None
    dependency_sources: tuple[str, ...] = ()
    dependency_conflicts: tuple[str, ...] = ()
    dependencies: tuple[tuple[str, str, str, str], ...] = ()
