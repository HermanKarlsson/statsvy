"""Aggregated dependency information for a project.

This module defines an immutable data structure for collecting and reporting
all dependencies found in a project, without any business logic.
"""

from dataclasses import dataclass

from statsvy.data.dependency import Dependency


@dataclass(frozen=True, slots=True)
class DependencyInfo:
    """Aggregated dependency information for a project.

    Contains all dependencies from a project, along with counts by category,
    source file tracking, and conflict detection information.

    Attributes:
        dependencies: Tuple of all dependencies found.
        prod_count: Number of production dependencies.
        dev_count: Number of development dependencies.
        optional_count: Number of optional dependencies.
        total_count: Total number of dependencies (should equal sum of counts).
        sources: Tuple of source file names that contributed dependencies.
        conflicts: Tuple of conflict descriptions (e.g., version mismatches
            between files).
    """

    dependencies: tuple[Dependency, ...]
    prod_count: int
    dev_count: int
    optional_count: int
    total_count: int
    sources: tuple[str, ...]
    conflicts: tuple[str, ...]
